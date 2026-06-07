"""
scraper.py
==========
Cricket Match Data Scraper – HowStat.com
-----------------------------------------
Collects the last 10 completed Test matches for England and India,
visits each scorecard, finds the top scorer, and writes match_data.csv.

Requirements
------------
    pip install cloudscraper beautifulsoup4 pandas

Usage
-----
    python scraper.py                  # England + India (default)
    python scraper.py ENG              # England only
    python scraper.py IND              # India only
    python scraper.py ENG IND          # both (explicit)

Output
------
    match_data.csv   – 20 rows (10 per country), header excluded from count
"""

import sys
import re
import time
import logging
from datetime import datetime

import cloudscraper
import pandas as pd
from bs4 import BeautifulSoup

print("SCRIPT STARTED")
print(__file__)
print("MAIN FILE LOADED")

# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────────────────────────
BASE  = "https://www.howstat.com/Cricket/Statistics/Matches"
MATCH_LIST_URL = BASE + "/MatchListCountry.asp"
SCORECARD_URL  = BASE + "/MatchScorecard.asp"

# Country codes supported by HowStat MatchListCountry page
COUNTRY_CODES: dict[str, str] = {
    "ENG": "England",
    "IND": "India",
    "AUS": "Australia",
    "PAK": "Pakistan",
    "SA":  "South Africa",
    "NZ":  "New Zealand",
    "SL":  "Sri Lanka",
    "WI":  "West Indies",
    "BAN": "Bangladesh",
    "ZIM": "Zimbabwe",
    "AFG": "Afghanistan",
    "IRE": "Ireland",
}

MATCH_LIMIT   = 10      # matches to collect per country
REQUEST_DELAY = 1.5     # seconds between requests (polite crawling)
TODAY         = datetime.today()

# Result must contain one of these words to be counted as completed
COMPLETED_RE = re.compile(r'\b(won|draw|drawn|tied)\b', re.IGNORECASE)

# Result containing any of these → in-progress / future → skip
EXCLUDE_RE = re.compile(
    r'(day\s+\d|stumps|in\s*progress|require|scheduled|upcoming|'
    r'future|abandoned|no\s+result|match\s+delayed|rain|bad\s+light|'
    r'yet\s+to\s+bat|to\s+bat)',
    re.IGNORECASE,
)

OUTPUT_COLUMNS = [
    "Sl No.", "Match Date", "Team 1", "Team 2",
    "Stadium Name", "Stadium Location",
    "Match Result", "Top Scorer Name", "Top Scorer Runs",
]

# ── HTTP session (cloudscraper bypasses Cloudflare JS challenges) ──────────────
_scraper = cloudscraper.create_scraper(
    browser={"browser": "chrome", "platform": "windows", "mobile": False}
)


def get(url: str, params: dict = None) -> BeautifulSoup:
    """Fetch URL, return BeautifulSoup. Raises on HTTP error."""
    time.sleep(REQUEST_DELAY)
    log.debug("GET %s  params=%s", url, params)
    resp = _scraper.get(url, params=params, timeout=25)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "html.parser")


# ── Date helpers ───────────────────────────────────────────────────────────────
_DATE_FMTS = (
    "%d/%m/%Y",       # 04/01/2026  – match list format
    "%d %B, %Y",      # 4th January, 2026  – scorecard format (after stripping ordinal)
    "%B %d, %Y",      # January 4, 2026
    "%d-%m-%Y",
    "%Y-%m-%d",
)


def _strip_ordinal(s: str) -> str:
    """'4th January, 2026' → '4 January, 2026'"""
    return re.sub(r'(\d+)(st|nd|rd|th)', r'\1', s)


def parse_date(raw: str) -> datetime | None:
    raw = _strip_ordinal(raw.strip())
    for fmt in _DATE_FMTS:
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue
    return None


def fmt_date(dt: datetime | None, raw: str) -> str:
    if dt:
        return dt.strftime("%d/%m/%Y")
    return raw.strip()


# ── Match-list parsing ─────────────────────────────────────────────────────────

def is_completed(result: str) -> bool:
    """True only if the result string indicates a finished match."""
    if EXCLUDE_RE.search(result):
        return False
    return bool(COMPLETED_RE.search(result))


def fetch_match_list(country_code: str) -> list[dict]:
    """
    Fetch the MatchListCountry page for a country and return a list of
    completed matches, sorted newest-first, limited to MATCH_LIMIT.

    Each dict: {date_dt, date_raw, match_code, result}
    """
    log.info("  Fetching match list for %s …", country_code)
    params = {"A": country_code, "B": "XXX", "C": "XXX"}
    soup = get(MATCH_LIST_URL, params=params)

    rows = soup.find_all("tr")
    log.info("  %d table rows found.", len(rows))

    candidates: list[dict] = []

    for row in rows:
        cells = row.find_all("td")
        # Expected columns: # | Date | Series(link) | Stadium | Result
        if len(cells) < 5:
            continue

        date_raw   = cells[1].get_text(strip=True)
        result_raw = cells[4].get_text(strip=True)
        link_tag   = cells[2].find("a", href=True)

        # Must have a scorecard link
        if not link_tag:
            continue

        href = link_tag["href"]  # e.g. "MatchScorecard.asp?MatchCode=2639"
        match_code_m = re.search(r'MatchCode=(\d+)', href, re.IGNORECASE)
        if not match_code_m:
            continue
        match_code = match_code_m.group(1)

        # Filter: completed only
        if not is_completed(result_raw):
            log.debug("    SKIP (not complete): %s | %s", date_raw, result_raw[:50])
            continue

        # Filter: not future
        dt = parse_date(date_raw)
        if dt and dt > TODAY:
            log.debug("    SKIP (future): %s", date_raw)
            continue

        candidates.append({
            "date_dt":    dt,
            "date_raw":   date_raw,
            "match_code": match_code,
            "result_raw": result_raw,
        })

    # Sort newest → oldest
    candidates.sort(
        key=lambda m: m["date_dt"] if m["date_dt"] else datetime.min,
        reverse=True,
    )

    selected = candidates[:MATCH_LIMIT]
    log.info("  → %d completed matches selected (from %d candidates).",
             len(selected), len(candidates))
    return selected


# ── Scorecard parsing ──────────────────────────────────────────────────────────

def _max_runs_in_bat_grid(grid) -> tuple[str, int]:
    """
    Scan a single scorecard-bat-grid div and return (player_name, runs)
    for the highest scorer.
    """
    best_name = ""
    best_runs = -1

    # Strategy 1: explicit class="runs" / class="name" spans
    rows = grid.find_all(class_=re.compile(r'bat[-_]?row', re.I)) or grid.find_all("tr")

    # If no explicit rows, fall back to all text nodes in the grid
    if not rows:
        rows = [grid]

    for row in rows:
        # Try structured spans first
        name_tag = (
            row.find(class_=re.compile(r'(name|player)', re.I))
            or row.find("a")
        )
        runs_tag = row.find(class_=re.compile(r'(runs?|score)', re.I))

        if name_tag and runs_tag:
            runs_text = runs_tag.get_text(strip=True).replace("*", "").strip()
            if runs_text.isdigit():
                r = int(runs_text)
                if r > best_runs:
                    best_runs = r
                    best_name = name_tag.get_text(strip=True)
            continue

        # Fallback: scan all td/span children for a number
        all_cells = row.find_all(["td", "span", "div"])
        for i, cell in enumerate(all_cells):
            txt = cell.get_text(strip=True).replace("*", "")
            if txt.isdigit() and i > 0:
                runs = int(txt)
                if runs > best_runs:
                    # Player name is most likely in the previous sibling cell
                    best_runs = runs
                    prev = all_cells[i - 1].get_text(strip=True)
                    best_name = prev if prev else best_name

    return best_name, best_runs


def fetch_scorecard(match_code: str) -> dict:
    """
    Open the scorecard for match_code.

    Returns a dict with keys:
        match_date, team1, team2, stadium_name, stadium_location,
        match_result, top_scorer_name, top_scorer_runs
    """
    log.info("      Scorecard MatchCode=%s …", match_code)
    soup = get(SCORECARD_URL, params={"MatchCode": match_code})

    result: dict = {
        "match_date":       "",
        "team1":            "",
        "team2":            "",
        "stadium_name":     "",
        "stadium_location": "",
        "match_result":     "",
        "top_scorer_name":  "N/A",
        "top_scorer_runs":  0,
    }

    # ── Venue ──────────────────────────────────────────────────────────────────
    header_div = soup.find(class_=re.compile(r'scorecard[-_]?header', re.I))
    if header_div:
        venue_full = header_div.get_text(strip=True)
        parts = venue_full.split(",", 1)
        result["stadium_name"]     = parts[0].strip()
        result["stadium_location"] = parts[1].strip() if len(parts) > 1 else ""

    # ── Teams and match date ───────────────────────────────────────────────────
    top_grid = soup.find(class_=re.compile(r'scorecard[-_]?top[-_]?grid', re.I))
    if top_grid:
        # Team names
        team_tags = top_grid.find_all(class_=re.compile(r'team[-_]?name', re.I))
        if len(team_tags) >= 2:
            result["team1"] = team_tags[0].get_text(strip=True)
            result["team2"] = team_tags[1].get_text(strip=True)
        else:
            # Fallback: grab all text chunks and infer
            texts = [t.strip() for t in top_grid.stripped_strings if t.strip() and t.strip() != "v"]
            if len(texts) >= 2:
                result["team1"] = texts[0]
                result["team2"] = texts[1]

        # Date
        date_tag = top_grid.find(class_=re.compile(r'(match[-_]?date|date)', re.I))
        if date_tag:
            result["match_date"] = date_tag.get_text(strip=True)
        else:
            # Look for a string that looks like a date
            for chunk in top_grid.stripped_strings:
                if re.search(r'\d{4}', chunk):
                    result["match_date"] = chunk.strip()
                    break

    # ── Match result ───────────────────────────────────────────────────────────
    result_tag = (
        soup.find(id=re.compile(r'result', re.I))
        or soup.find(class_=re.compile(r'result', re.I))
    )
    if result_tag:
        result["match_result"] = result_tag.get_text(strip=True)

    # ── Top scorer: scan ALL scorecard-bat-grid divs ───────────────────────────
    bat_grids = soup.find_all(class_=re.compile(r'scorecard[-_]?bat[-_]?grid', re.I))

    if not bat_grids:
        # Wider fallback: any table on the page that looks like a batting table
        bat_grids = []
        for tbl in soup.find_all("table"):
            header = tbl.find("tr")
            if header:
                headers_text = header.get_text().lower()
                if "runs" in headers_text or " r " in headers_text:
                    bat_grids.append(tbl)

    overall_best_name = "N/A"
    overall_best_runs = 0

    for grid in bat_grids:
        name, runs = _max_runs_in_bat_grid(grid)
        if runs > overall_best_runs:
            overall_best_runs = runs
            overall_best_name = name

    result["top_scorer_name"] = overall_best_name
    result["top_scorer_runs"] = overall_best_runs

    log.info(
        "        → %s v %s | Top: %s (%s)",
        result["team1"], result["team2"],
        result["top_scorer_name"], result["top_scorer_runs"],
    )
    return result


# ── Main pipeline ──────────────────────────────────────────────────────────────

def scrape_country(code: str) -> pd.DataFrame:
    """Full pipeline for one country. Returns a DataFrame."""
    country_name = COUNTRY_CODES.get(code.upper(), code.upper())
    log.info("")
    log.info("=" * 60)
    log.info("  COUNTRY: %s  (%s)", country_name, code.upper())
    log.info("=" * 60)

    # Step 1-4: get last 10 completed match codes
    matches = fetch_match_list(code.upper())
    if not matches:
        log.warning("  No completed matches found for %s.", country_name)
        return pd.DataFrame(columns=OUTPUT_COLUMNS)

    rows = []
    for sl, m in enumerate(matches, 1):
        log.info("  [%d/%d] %s — MatchCode %s",
                 sl, len(matches), m["date_raw"], m["match_code"])

        # Step 5-7: open scorecard, extract details + top scorer
        sc = fetch_scorecard(m["match_code"])

        # Prefer scorecard date; fall back to list date
        display_date = fmt_date(parse_date(sc["match_date"]), m["date_raw"]) \
                       if sc["match_date"] else fmt_date(m["date_dt"], m["date_raw"])

        rows.append({
            "Sl No.":            sl,
            "Match Date":        display_date,
            "Team 1":            sc["team1"]            or "N/A",
            "Team 2":            sc["team2"]            or "N/A",
            "Stadium Name":      sc["stadium_name"]     or "N/A",
            "Stadium Location":  sc["stadium_location"] or "N/A",
            "Match Result":      sc["match_result"]     or m["result_raw"],
            "Top Scorer Name":   sc["top_scorer_name"],
            "Top Scorer Runs":   sc["top_scorer_runs"],
        })

    df = pd.DataFrame(rows, columns=OUTPUT_COLUMNS)
    log.info("  Done. %d rows for %s.", len(df), country_name)
    return df


def main(codes: list[str]) -> None:
    all_frames: list[pd.DataFrame] = []

    for code in codes:
        df = scrape_country(code)
        if not df.empty:
            all_frames.append(df)
        else:
            log.warning("  Skipping %s — no data.", code)

    if not all_frames:
        log.error("No data collected. Check internet connection or site availability.")
        return

    # Combine and reset Sl No. per-country (kept separate, not global)
    combined = pd.concat(all_frames, ignore_index=True)

    out_file = "match_data.csv"
    combined.to_csv(out_file, index=False, encoding="utf-8-sig")
    log.info("")
    log.info("✅  Saved %d rows → %s", len(combined), out_file)

    # Pretty-print to terminal
    for code, df in zip(codes, all_frames):
        country = COUNTRY_CODES.get(code.upper(), code.upper())
        print(f"\n{'='*70}")
        print(f"  {country} – Last {len(df)} Completed Test Matches")
        print(f"{'='*70}")
        print(df.to_string(index=False))


if __name__ == "__main__":
    # Accept country codes as CLI args; default to England + India
    codes = [a.upper() for a in sys.argv[1:]] if len(sys.argv) > 1 else ["ENG", "IND"]

    # Validate
    unknown = [c for c in codes if c not in COUNTRY_CODES]
    if unknown:
        print(f"Unknown country code(s): {unknown}")
        print(f"Valid codes: {', '.join(sorted(COUNTRY_CODES))}")
        sys.exit(1)

    main(codes)