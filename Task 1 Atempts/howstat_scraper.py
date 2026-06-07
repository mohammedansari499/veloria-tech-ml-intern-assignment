"""
howstat_scraper.py
==================
Scrapes the latest 10 completed matches for England and India from
www.howstat.com and writes match_data.csv (20 data rows).

Dependencies:
    pip install selenium beautifulsoup4 pandas webdriver-manager

Usage:
    python howstat_scraper.py

Chrome (or Chromium) must be installed on the system.
The script auto-downloads the matching ChromeDriver via webdriver-manager.
"""

from __future__ import annotations

import time
import re
from datetime import datetime

import pandas as pd
from bs4 import BeautifulSoup


# ─────────────────────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────────────────────

MATCH_LIST_URL = "https://www.howstat.com/Cricket/Statistics/Matches/MatchListCountry.asp"
BASE_URL       = "https://www.howstat.com"
COUNTRIES      = ["England", "India"]
TARGET_MATCHES = 10
PAGE_DELAY     = 1.5        # seconds between page loads
OUTPUT_FILE    = "match_data.csv"

CSV_COLUMNS = [
    "Sl No.",
    "Match Date",
    "Team 1",
    "Team 2",
    "Stadium Name",
    "Stadium Location",
    "Match Result",
    "Top Scorer Name",
    "Top Scorer Runs",
]

# ─────────────────────────────────────────────────────────────────────────────
# DRIVER SETUP
# ─────────────────────────────────────────────────────────────────────────────

def build_driver() -> webdriver.Chrome:
    opts = Options()

    # Disable headless for now
    # opts.add_argument("--headless=new")

    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1920,1080")

    opts.add_argument("--disable-blink-features=AutomationControlled")

    opts.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/136.0.0.0 Safari/537.36"
    )

    service = Service(ChromeDriverManager().install())

    driver = webdriver.Chrome(
        service=service,
        options=opts
    )

    driver.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )

    return driver


# ─────────────────────────────────────────────────────────────────────────────
# DATE PARSING
# ─────────────────────────────────────────────────────────────────────────────

DATE_FORMATS = [
    "%d %b %Y",   # 15 Mar 2025
    "%d/%m/%Y",   # 15/03/2025
    "%Y-%m-%d",   # 2025-03-15
    "%d-%b-%Y",   # 15-Mar-2025
    "%B %d, %Y",  # March 15, 2025
]

def parse_date(raw: str) -> datetime | None:
    raw = raw.strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            pass
    return None


# ─────────────────────────────────────────────────────────────────────────────
# STEP 1 – navigate to match list and select country
# ─────────────────────────────────────────────────────────────────────────────

def load_match_list(driver: webdriver.Chrome, country: str) -> BeautifulSoup:
    """
    Navigate to the Match List page, choose `country` from the dropdown,
    click Submit, and return the page source as BeautifulSoup.
    """
    print(f"\n{'='*60}")
    print(f"  Loading match list for: {country}")
    print(f"{'='*60}")

    driver.get(MATCH_LIST_URL)

    print("URL:", driver.current_url)
    print("TITLE:", driver.title)

    time.sleep(4)

    # Wait until dropdowns appear
    wait = WebDriverWait(driver, 15)

    wait.until(
        EC.presence_of_element_located((By.TAG_NAME, "select"))
    )

    time.sleep(2)

    # Get all dropdowns
    dropdowns = driver.find_elements(By.TAG_NAME, "select")

    print(f"Found {len(dropdowns)} dropdowns")

    for i, d in enumerate(dropdowns):
        print(
            f"Dropdown {i}: "
            f"name={d.get_attribute('name')} "
            f"id={d.get_attribute('id')}"
        )

    # First dropdown is country selector
    country_dropdown = Select(dropdowns[0])
    country_dropdown.select_by_visible_text(country)
    driver.execute_script(
        "arguments[0].dispatchEvent(new Event('change'));",
        dropdowns[0]
    )
    print(
        "Selected:",
        country_dropdown.first_selected_option.text
    )

    time.sleep(2)

    submit_btn = driver.find_element(
        By.XPATH,
        "//input[@type='submit' or @value='Submit']"
    )

    driver.execute_script(
        "arguments[0].click();",
        submit_btn
    )

    time.sleep(5)

    print("RESULT URL:", driver.current_url)
    print("RESULT TITLE:", driver.title)

    with open(
        f"result_{country}.html",
        "w",
        encoding="utf-8"
    ) as f:
        f.write(driver.page_source)

    return BeautifulSoup(driver.page_source, "html.parser")


# ─────────────────────────────────────────────────────────────────────────────
# STEP 2 – parse the match list table, filter completed matches
# ─────────────────────────────────────────────────────────────────────────────

SKIP_KEYWORDS = {
    "future", "scheduled", "no result", "abandoned",
    "cancelled", "canceled", "incomplete", "tbd", "tba",
}

def is_valid_result(result_text: str) -> bool:
    """Return True if result indicates a completed win or draw."""
    lower = result_text.lower().strip()
    if not lower:
        return False
    if any(kw in lower for kw in SKIP_KEYWORDS):
        return False
    return "won" in lower or "draw" in lower


def parse_match_rows(soup: BeautifulSoup) -> list[dict]:

    matches = []

    tables = soup.find_all("table")

    target_table = None

    for table in tables:

        text = table.get_text(" ", strip=True)

        if (
            "Date" in text
            and "Series" in text
            and "Ground" in text
            and "Result" in text
        ):
            target_table = table
            break

    if not target_table:
        return []

    rows = target_table.find_all("tr")

    for tr in rows:

        cells = tr.find_all("td")

        if len(cells) < 5:
            continue

        try:
            date_str = cells[1].get_text(strip=True)

            series_link = cells[2].find("a")

            if not series_link:
                continue

            series_text = series_link.get_text(strip=True)

            href = series_link.get("href", "")

            if href and not href.startswith("http"):
                href = BASE_URL + "/" + href.lstrip("/")

            result = cells[4].get_text(strip=True)

            result_lower = result.lower()

            # Skip live matches
            if "day " in result_lower:
                continue

            # Keep only completed matches
            if (
                "won" not in result_lower
                and "draw" not in result_lower
            ):
                continue

            matches.append(
                {
                    "date_str": date_str,
                    "team1": "",
                    "team2": "",
                    "result": result,
                    "link": href,
                }
            )

        except Exception:
            continue

    matches.reverse()

    return matches[:TARGET_MATCHES]


def extract_teams(cells: list, headers: list) -> tuple[str, str]:
    """
    Best-effort extraction of Team 1 and Team 2 from a row.
    Howstat sometimes uses columns named 'teams' or 'match', or two separate
    team columns.  Falls back to positional guesses.
    """
    # Try named columns first
    for keyword in ("team 1", "home", "team1"):
        idx = next((i for i, h in enumerate(headers) if keyword in h), None)
        if idx is not None and idx < len(cells):
            t1 = cells[idx].get_text(strip=True)
            break
    else:
        t1 = cells[1].get_text(strip=True) if len(cells) > 1 else ""

    for keyword in ("team 2", "away", "team2"):
        idx = next((i for i, h in enumerate(headers) if keyword in h), None)
        if idx is not None and idx < len(cells):
            t2 = cells[idx].get_text(strip=True)
            break
    else:
        t2 = cells[2].get_text(strip=True) if len(cells) > 2 else ""

    # If a single "teams" / "match" column has "v" or "vs", split on it
    for keyword in ("teams", "match", "versus"):
        idx = next((i for i, h in enumerate(headers) if keyword in h), None)
        if idx is not None and idx < len(cells):
            combined = cells[idx].get_text(strip=True)
            for sep in (" v ", " vs ", " V ", " VS "):
                if sep in combined:
                    parts = combined.split(sep, 1)
                    return parts[0].strip(), parts[1].strip()

    return t1, t2


# ─────────────────────────────────────────────────────────────────────────────
# STEP 3 – open each scorecard and extract match details
# ─────────────────────────────────────────────────────────────────────────────

def fetch_scorecard(driver: webdriver.Chrome, url: str) -> BeautifulSoup:
    """Navigate to a scorecard URL and return its BeautifulSoup."""
    driver.get(url)
    time.sleep(PAGE_DELAY)
    return BeautifulSoup(driver.page_source, "html.parser")


# ── venue ─────────────────────────────────────────────────────────────────────

VENUE_LABELS = ("venue", "ground", "stadium", "played at", "location")

def extract_venue(soup: BeautifulSoup) -> tuple[str, str]:
    """
    Return (stadium_name, stadium_location).
    Howstat renders venue info in a header block, often as:
        Venue : Stadium Name, City, Country
    or in a table cell labelled 'Venue'.
    """
    full_text = ""

    # 1. Look for a <td> or <th> whose text starts with a venue keyword,
    #    then grab the adjacent cell or the text after the colon.
    for tag in soup.find_all(["td", "th", "span", "p", "div", "b", "strong"]):
        txt = tag.get_text(strip=True)
        lower = txt.lower()
        for label in VENUE_LABELS:
            if lower.startswith(label):
                # Try sibling cell
                next_td = tag.find_next_sibling(["td", "th"])
                if next_td:
                    full_text = next_td.get_text(strip=True)
                    break
                # Try colon split in same string
                if ":" in txt:
                    full_text = txt.split(":", 1)[1].strip()
                    break
        if full_text:
            break

    # 2. Fallback: search all page text for a line containing "Venue"
    if not full_text:
        page_text = soup.get_text(separator="\n")
        for line in page_text.splitlines():
            stripped = line.strip()
            if stripped.lower().startswith("venue") and ":" in stripped:
                full_text = stripped.split(":", 1)[1].strip()
                break

    if not full_text:
        return "N/A", "N/A"

    # Split "Stadium Name, City" or "Stadium Name, City, Country"
    parts = [p.strip() for p in full_text.split(",")]
    name     = parts[0] if parts else "N/A"
    location = ", ".join(parts[1:]) if len(parts) > 1 else "N/A"
    return name, location


# ── batting table → top scorer ────────────────────────────────────────────────

def parse_batting_table(table_tag) -> tuple[str, int]:
    """
    Given a <table> BeautifulSoup tag that looks like a batting scorecard,
    find the player with the highest value in the 'R' (Runs) column.
    Returns (player_name, runs_int).  Returns ("N/A", -1) if nothing found.
    """
    # Find the header row to locate the 'R' column index
    header_row = table_tag.find("tr")
    if not header_row:
        return "N/A", -1

    headers = [th.get_text(strip=True) for th in header_row.find_all(["th", "td"])]
    # 'R' is typically a standalone column; avoid matching 'RO' or 'Runs' etc.
    r_idx = next(
        (i for i, h in enumerate(headers) if re.fullmatch(r"R", h.strip())),
        None
    )
    if r_idx is None:
        return "N/A", -1

    # Player name is expected in the first column (index 0)
    best_name = "N/A"
    best_runs = -1

    for tr in table_tag.find_all("tr")[1:]:
        cells = tr.find_all(["td", "th"])
        if len(cells) <= r_idx:
            continue
        runs_raw = cells[r_idx].get_text(strip=True).replace("*", "").replace("†", "").strip()
        try:
            runs_int = int(runs_raw)
        except ValueError:
            continue

        if runs_int > best_runs:
            best_runs = runs_int
            # Name cell may contain a hyperlink; get_text() handles that
            best_name = cells[0].get_text(strip=True)

    return best_name, best_runs


def extract_top_scorer(soup: BeautifulSoup) -> tuple[str, int]:
    """
    Locate all batting scorecards on the page (one per team / innings).
    Compare best scorers across all of them and return the overall top scorer.
    """
    overall_best_name = "N/A"
    overall_best_runs = -1

    for table in soup.find_all("table"):
        ths = [th.get_text(strip=True) for th in table.find_all(["th", "td"])[:15]]
        # A batting table will have an 'R' header somewhere in the first few columns
        has_r_col = any(re.fullmatch(r"R", h.strip()) for h in ths)
        if not has_r_col:
            continue

        name, runs = parse_batting_table(table)
        if runs > overall_best_runs:
            overall_best_runs = runs
            overall_best_name = name

    return overall_best_name, overall_best_runs


# ─────────────────────────────────────────────────────────────────────────────
# STEP 4 – collect 10 completed matches for one country
# ─────────────────────────────────────────────────────────────────────────────

def collect_country_matches(driver: webdriver.Chrome, country: str, sl_offset: int) -> list[dict]:
    """
    Full pipeline for one country:
      1. Load match list
      2. Filter valid completed matches (descending date)
      3. For each match open scorecard, extract all fields
    Returns a list of row-dicts ready for the DataFrame.
    """
    list_soup = load_match_list(driver, country)

    with open(
        f"parsed_page_{country}.html",
        "w",
        encoding="utf-8"
    ) as f:
        f.write(str(list_soup))

    all_matches = parse_match_rows(list_soup)

    if not all_matches:
        print(f"  [WARNING] No matches parsed for {country}. "
              "The table structure may have changed.")

    records: list[dict] = []
    collected = 0

    for m in all_matches:
        if collected >= TARGET_MATCHES:
            break

        print(f"\n  [{country}] Match {sl_offset + collected + 1}: "
              f"{m['date_str']}  {m['team1']} vs {m['team2']}")
        print(f"    Result : {m['result']}")
        print(f"    URL    : {m['link']}")

        if not m["link"]:
            print("    [SKIP] No scorecard URL found.")
            continue

        try:
            scorecard = fetch_scorecard(driver, m["link"])
        except Exception as exc:
            print(f"    [SKIP] Failed to load scorecard: {exc}")
            continue

        stadium_name, stadium_location = extract_venue(scorecard)
        top_name, top_runs             = extract_top_scorer(scorecard)

        print(f"    Venue  : {stadium_name}, {stadium_location}")
        print(f"    Top scorer: {top_name} ({top_runs} runs)")

        records.append({
            "Sl No.":           sl_offset + collected + 1,
            "Country":          country,
            "Match Date":       m["date_str"],
            "Team 1":           m["team1"],
            "Team 2":           m["team2"],
            "Stadium Name":     stadium_name,
            "Stadium Location": stadium_location,
            "Match Result":     m["result"],
            "Top Scorer Name":  top_name,
            "Top Scorer Runs":  top_runs if top_runs >= 0 else "N/A",
        })
        collected += 1

    print(f"\n  [{country}] Collected {collected} / {TARGET_MATCHES} matches.")
    return records


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  HowStat Cricket Scraper")
    print(f"  Run time : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    driver = build_driver()
    all_records: list[dict] = []

    try:
        for idx, country in enumerate(COUNTRIES):
            sl_offset = idx * TARGET_MATCHES
            rows = collect_country_matches(driver, country, sl_offset)
            all_records.extend(rows)
    finally:
        driver.quit()
        print("\n  Browser closed.")

    if not all_records:
        print("\n  [ERROR] No records collected. Check the site structure.")
        return

    df = pd.DataFrame(all_records, columns=CSV_COLUMNS)
    df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")

    print(f"\n{'='*60}")
    print(f"  Saved {len(df)} rows → {OUTPUT_FILE}")
    print("=" * 60)
    print(df.to_string(index=False))


if __name__ == "__main__":
    main()