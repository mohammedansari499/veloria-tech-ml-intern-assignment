"""
scraper.py
==========
HowStat.com — Test Match Data Scraper
--------------------------------------
Collects the last 10 completed Test matches for England and India,
visits each scorecard, extracts top scorer, and writes match_data.csv.

HTML structure confirmed from live page dumps:
  Match list  : table.TableLined  — cols: [#, date, series-link, ground, result-span]
  Scorecard   : table.ScorecardHeaderTable — ScorecardHeader cells (series, venue, date, result)
                td.ScorecardCountry1 / ScorecardCountry2 — team names
                td.ScorecardPlayer — batting player name
                runs in 3rd TextBlack9 td of each player row (inside <b> tag)

Requirements
------------
    pip install requests beautifulsoup4 pandas

Usage
-----
    python scraper.py                  # England + India (default)
    python scraper.py ENG              # England only
    python scraper.py ENG IND AUS      # multiple countries

Output
------
    match_data.csv
"""

import sys
import re
import time
import logging
from datetime import datetime

import requests
from bs4 import BeautifulSoup
import pandas as pd

# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────────────────────────
MATCH_LIST_URL = "https://www.howstat.com/Cricket/Statistics/Matches/MatchListCountry.asp"
SCORECARD_URL  = "https://www.howstat.com/Cricket/Statistics/Matches/MatchScorecard.asp"

# Exact country codes from the HowStat dropdown
COUNTRY_CODES = {
    "ENG": "England",
    "IND": "India",
    "AUS": "Australia",
    "PAK": "Pakistan",
    "SAF": "South Africa",
    "NZL": "New Zealand",
    "SRL": "Sri Lanka",
    "WIN": "West Indies",
    "BAN": "Bangladesh",
    "ZIM": "Zimbabwe",
    "AFG": "Afghanistan",
    "IRE": "Ireland",
}

MATCH_LIMIT   = 10
REQUEST_DELAY = 1.5   # seconds between requests — be polite
TODAY         = datetime.today()

# A completed match result contains one of these words
COMPLETED_RE = re.compile(r'\b(won|draw|drawn|tied)\b', re.IGNORECASE)

# Skip rows whose result contains any of these (future / in-progress / void)
SKIP_RE = re.compile(
    r'(day\s+\d|stumps|in\s*progress|require|scheduled|upcoming|'
    r'abandoned|no\s+result|delayed|bad\s+light|future)',
    re.IGNORECASE,
)

# These are non-player rows in the batting table — must be skipped when finding top scorer
SKIP_BATTING_ROW = re.compile(
    r'^(extras?|total|fall\s+of|did\s+not\s+bat|dnb|yet\s+to\s+bat)',
    re.IGNORECASE,
)

OUTPUT_COLS = [
    "Sl No.", "Match Date", "Team 1", "Team 2",
    "Stadium Name", "Stadium Location",
    "Match Result", "Top Scorer Name", "Top Scorer Runs",
]

# ── HTTP session ───────────────────────────────────────────────────────────────
SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.howstat.com/",
})


def get_soup(url: str, params: dict = None) -> BeautifulSoup:
    """Fetch URL and return a BeautifulSoup object. Raises on HTTP error."""
    time.sleep(REQUEST_DELAY)
    resp = SESSION.get(url, params=params, timeout=30)
    resp.raise_for_status()
    # HowStat uses windows-1252 encoding
    resp.encoding = "windows-1252"
    return BeautifulSoup(resp.text, "html.parser")


# ── Date helpers ───────────────────────────────────────────────────────────────
def parse_date(raw: str) -> datetime | None:
    """Try several date formats; return datetime or None."""
    raw = raw.strip()
    # Strip ordinal suffixes: "4th" → "4"
    raw = re.sub(r'(\d+)(st|nd|rd|th)\b', r'\1', raw)
    for fmt in ("%d/%m/%Y", "%d %B, %Y", "%d %B %Y", "%B %d, %Y"):
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue
    return None


# ── Match list ─────────────────────────────────────────────────────────────────
def fetch_match_list(country_code: str) -> list[dict]:
    """
    Return up to MATCH_LIMIT completed matches for country_code,
    sorted newest-first.

    Each dict: {date_str, match_code, series, ground, result}
    """
    log.info("Fetching match list for %s (%s)…",
             COUNTRY_CODES.get(country_code, country_code), country_code)

    soup = get_soup(MATCH_LIST_URL, params={"A": country_code, "B": "XXX", "C": "XXX"})

    # The match data lives in table.TableLined
    table = soup.find("table", class_="TableLined")
    if not table:
        log.error("  Could not find TableLined — page structure may have changed.")
        return []

    rows = table.find_all("tr")
    log.info("  Found %d rows in match table.", len(rows))

    candidates = []
    for row in rows:
        cells = row.find_all("td")
        # Expect at least 5 cells: [#, date, series-link, ground, result]
        if len(cells) < 5:
            continue

        date_raw = cells[1].get_text(strip=True)

        # Series link — extract MatchCode from href
        series_link = cells[2].find("a", href=True)
        if not series_link:
            continue
        href = series_link["href"]
        match_code_m = re.search(r'MatchCode=(\w+)', href, re.IGNORECASE)
        if not match_code_m:
            continue
        match_code = match_code_m.group(1)
        series_name = series_link.get_text(strip=True)

        # Ground name
        ground_tag = cells[3].find("a")
        ground = ground_tag.get_text(strip=True) if ground_tag else cells[3].get_text(strip=True)

        # Result (inside a <span>)
        result_raw = cells[4].get_text(strip=True)

        # Only keep completed, non-future matches
        if SKIP_RE.search(result_raw):
            continue
        if not COMPLETED_RE.search(result_raw):
            continue

        dt = parse_date(date_raw)
        if dt and dt > TODAY:
            continue  # future match

        candidates.append({
            "date_dt":    dt,
            "date_str":   date_raw,
            "match_code": match_code,
            "series":     series_name,
            "ground":     ground,
            "result":     result_raw,
        })

    # Sort newest → oldest and take the first MATCH_LIMIT
    candidates.sort(
        key=lambda m: m["date_dt"] if m["date_dt"] else datetime.min,
        reverse=True,
    )
    selected = candidates[:MATCH_LIMIT]
    log.info("  Selected %d completed matches (from %d candidates).",
             len(selected), len(candidates))
    return selected


# ── Scorecard ──────────────────────────────────────────────────────────────────
def fetch_scorecard(match_code: str) -> dict:
    """
    Open the scorecard for match_code and extract:
        team1, team2, stadium_name, stadium_location,
        match_date, match_result, top_scorer_name, top_scorer_runs

    HTML layout (confirmed from live page):
      table.ScorecardHeaderTable
        tr[0] td.ScorecardHeader  → "Series name - Nth Test"
        tr[1] td.ScorecardHeader  → "Stadium Name, City"
        tr[2] td.ScorecardHeader  → "4th January, 2026"
        tr[3] td                  → team flags / names table
                 td.ScorecardCountry1 → Team 1 name
                 td.ScorecardCountry2 → Team 2 name
        tr[4] td.ScorecardHeader  → "Australia won by 5 wickets"

      Batting rows: td.ScorecardPlayer (name) + following TextBlack9 cells
                    Runs are in the 3rd TextBlack9 cell, wrapped in <b>
    """
    log.info("    Scorecard %s …", match_code)
    soup = get_soup(SCORECARD_URL, params={"MatchCode": match_code})

    result = {
        "team1":            "N/A",
        "team2":            "N/A",
        "stadium_name":     "N/A",
        "stadium_location": "N/A",
        "match_date":       "N/A",
        "match_result":     "N/A",
        "top_scorer_name":  "N/A",
        "top_scorer_runs":  0,
    }

    # ── Header table ────────────────────────────────────────────────────────────
    header_table = soup.find("table", class_="ScorecardHeaderTable")
    if header_table:
        header_cells = header_table.find_all("td", class_="ScorecardHeader")

        # header_cells[0] = series title, [1] = venue, [2] = date
        # The last ScorecardHeader cell in the table is the result
        if len(header_cells) >= 3:
            # Venue: "Sydney Cricket Ground, Sydney"
            venue_text = header_cells[1].get_text(strip=True)
            if "," in venue_text:
                parts = venue_text.split(",", 1)
                result["stadium_name"]     = parts[0].strip()
                result["stadium_location"] = parts[1].strip()
            else:
                result["stadium_name"] = venue_text

            # Date
            result["match_date"] = header_cells[2].get_text(strip=True)

            # Result is the last ScorecardHeader cell
            result["match_result"] = header_cells[-1].get_text(strip=True)

        # Team names
        team1_tag = header_table.find("td", class_="ScorecardCountry1")
        team2_tag = header_table.find("td", class_="ScorecardCountry2")
        if team1_tag:
            result["team1"] = team1_tag.get_text(strip=True)
        if team2_tag:
            result["team2"] = team2_tag.get_text(strip=True)

    # ── Batting: find top scorer across all innings ─────────────────────────────
    # Each batting row: first cell = td.ScorecardPlayer (player name link)
    # The RUNS column is the 3rd data cell (TextBlack9) — it contains <b>runs</b>
    best_name = "N/A"
    best_runs = 0

    player_cells = soup.find_all("td", class_="ScorecardPlayer")
    for cell in player_cells:
        player_name = cell.get_text(strip=True)

        # Skip non-player rows just in case
        if SKIP_BATTING_ROW.match(player_name):
            continue

        # Walk to the parent row and collect TextBlack9 cells after the player cell
        row = cell.find_parent("tr")
        if not row:
            continue

        # All TextBlack9 tds in this row
        data_cells = row.find_all("td", class_="TextBlack9")
        # The runs cell is the 3rd one (index 2): dismissal info, R, BF, 4s, 6s…
        # Runs are inside a <b> tag in that cell
        if len(data_cells) < 3:
            continue

        runs_cell = data_cells[1]  # index 1 = the R column (after dismissal text)
        bold = runs_cell.find("b")
        if bold:
            runs_text = bold.get_text(strip=True).replace("*", "").strip()
        else:
            runs_text = runs_cell.get_text(strip=True).replace("*", "").strip()

        if runs_text.isdigit():
            runs = int(runs_text)
            if runs > best_runs:
                best_runs = runs
                best_name = player_name

    result["top_scorer_name"] = best_name
    result["top_scorer_runs"] = best_runs

    log.info("      → %s v %s | %s | Top: %s (%d)",
             result["team1"], result["team2"],
             result["match_result"],
             result["top_scorer_name"], result["top_scorer_runs"])

    return result


# ── Country pipeline ───────────────────────────────────────────────────────────
def scrape_country(code: str) -> pd.DataFrame:
    """Run the full pipeline for one country. Returns a DataFrame."""
    country_name = COUNTRY_CODES.get(code.upper(), code.upper())
    log.info("")
    log.info("=" * 60)
    log.info("COUNTRY: %s (%s)", country_name, code.upper())
    log.info("=" * 60)

    matches = fetch_match_list(code.upper())
    if not matches:
        log.warning("No completed matches found for %s.", country_name)
        return pd.DataFrame(columns=OUTPUT_COLS)

    rows = []
    for sl, m in enumerate(matches, 1):
        log.info("  [%d/%d]  %s  —  MatchCode %s",
                 sl, len(matches), m["date_str"], m["match_code"])

        sc = fetch_scorecard(m["match_code"])

        # Use scorecard date if available, else fall back to list date
        display_date = m["date_str"]
        if sc["match_date"] != "N/A":
            dt = parse_date(sc["match_date"])
            if dt:
                display_date = dt.strftime("%d/%m/%Y")

        rows.append({
            "Sl No.":           sl,
            "Match Date":       display_date,
            "Team 1":           sc["team1"],
            "Team 2":           sc["team2"],
            "Stadium Name":     sc["stadium_name"],
            "Stadium Location": sc["stadium_location"],
            "Match Result":     sc["match_result"] if sc["match_result"] != "N/A" else m["result"],
            "Top Scorer Name":  sc["top_scorer_name"],
            "Top Scorer Runs":  sc["top_scorer_runs"],
        })

    df = pd.DataFrame(rows, columns=OUTPUT_COLS)
    log.info("Done. %d rows for %s.", len(df), country_name)
    return df


# ── Main ───────────────────────────────────────────────────────────────────────
def main(codes: list[str]) -> None:
    all_frames = []

    for code in codes:
        df = scrape_country(code)
        if not df.empty:
            all_frames.append(df)

    if not all_frames:
        log.error("No data collected. Check internet connection or site availability.")
        sys.exit(1)

    combined = pd.concat(all_frames, ignore_index=True)

    out_file = "match_data.csv"
    combined.to_csv(out_file, index=False, encoding="utf-8-sig")
    log.info("")
    log.info("Saved %d rows → %s", len(combined), out_file)

    # Print table to terminal
    for code, df in zip(codes, all_frames):
        country = COUNTRY_CODES.get(code.upper(), code.upper())
        print(f"\n{'='*80}")
        print(f"  {country} — Last {len(df)} Completed Test Matches")
        print(f"{'='*80}")
        print(df.to_string(index=False))
    print(f"\nSaved to {out_file}")


if __name__ == "__main__":
    codes = [a.upper() for a in sys.argv[1:]] if len(sys.argv) > 1 else ["ENG", "IND"]

    unknown = [c for c in codes if c not in COUNTRY_CODES]
    if unknown:
        print(f"Unknown country code(s): {unknown}")
        print(f"Valid codes: {', '.join(sorted(COUNTRY_CODES))}")
        sys.exit(1)

    main(codes)