"""
scraper.py  –  HowStat Cricket Match Scraper
============================================
Collects last 10 completed Test matches for England and India,
extracts team names, venue, result, and top scorer from each
scorecard, and writes match_data.csv.

Install:  pip install cloudscraper beautifulsoup4 pandas
Run:      python scraper.py
"""

import re
import time
import logging
from datetime import datetime

import cloudscraper
import pandas as pd
from bs4 import BeautifulSoup

# ── Config ─────────────────────────────────────────────────────────────────────
COUNTRIES = {
    "ENG": "England",
    "IND": "India",
}

MATCH_LIST_URL = "https://www.howstat.com/Cricket/Statistics/Matches/MatchListCountry.asp"
SCORECARD_URL  = "https://www.howstat.com/Cricket/Statistics/Matches/MatchScorecard.asp"
MATCH_LIMIT    = 10
DELAY          = 1.5   # seconds between requests

COMPLETED_RE = re.compile(r'\b(won|draw|drawn|tied)\b', re.I)
EXCLUDE_RE   = re.compile(
    r'(day\s*\d|stumps|in\s*progress|require|scheduled|abandoned|'
    r'no\s*result|yet\s*to\s*bat|upcoming|match\s*delayed|rain|bad\s*light)',
    re.I
)
TODAY = datetime.today()

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger()

sc = cloudscraper.create_scraper(
    browser={"browser": "chrome", "platform": "windows", "mobile": False}
)

# ── Helpers ────────────────────────────────────────────────────────────────────

def fetch(url, params):
    time.sleep(DELAY)
    r = sc.get(url, params=params, timeout=25)
    r.raise_for_status()
    return BeautifulSoup(r.text, "html.parser")


def is_done(result: str) -> bool:
    return bool(COMPLETED_RE.search(result)) and not EXCLUDE_RE.search(result)


# ── Step 1: Get last 10 completed match codes from match list ──────────────────

def get_match_list(code: str) -> list[dict]:
    log.info("[%s] Fetching match list …", code)
    soup = fetch(MATCH_LIST_URL, {"A": code, "B": "XXX", "C": "XXX"})

    matches = []
    for row in soup.find_all("tr"):
        cells = row.find_all("td")
        if len(cells) < 5:
            continue

        date_raw   = cells[1].get_text(strip=True)
        result_raw = cells[4].get_text(strip=True)
        link       = cells[2].find("a", href=True)
        if not link:
            continue

        mc = re.search(r'MatchCode=(\d+)', link["href"], re.I)
        if not mc:
            continue

        # Parse and validate date
        try:
            dt = datetime.strptime(date_raw, "%d/%m/%Y")
        except ValueError:
            continue

        if dt > TODAY or not is_done(result_raw):
            continue

        matches.append({"date": date_raw, "code": mc.group(1)})
        if len(matches) == MATCH_LIMIT:
            break

    log.info("[%s] Found %d completed matches.", code, len(matches))
    return matches


# ── Step 2: Parse each scorecard ───────────────────────────────────────────────

# Rows to skip when scanning batting tables
SKIP_ROW = re.compile(
    r'^(extras|total|did\s*not\s*bat|dnb|fall\s*of|fow|yet\s*to\s*bat|bowling)$',
    re.I
)


def parse_scorecard(match_code: str) -> dict:
    soup = fetch(SCORECARD_URL, {"MatchCode": match_code})

    result = {
        "team1": "N/A", "team2": "N/A",
        "stadium": "N/A", "location": "N/A",
        "date": "N/A", "match_result": "N/A",
        "top_scorer": "N/A", "top_runs": 0,
    }

    # ── Series title → team names ──────────────────────────────────────────────
    # HowStat uses class="FormHeadingDark" for the series row
    # e.g. "2025-2026 Australia v England - 5th Test"
    heading = soup.find(class_="FormHeadingDark")
    if heading:
        m = re.search(
            r'\b([A-Z][A-Za-z\s]+?)\s+v\.?\s+([A-Z][A-Za-z\s]+?)(?:\s*[-–]\s*\d|\s*$)',
            heading.get_text(strip=True)
        )
        if m:
            result["team1"] = m.group(1).strip()
            result["team2"] = m.group(2).strip()

    # ── Venue, location, date, result ─────────────────────────────────────────
    # HowStat uses class="FormHeading" for stadium / city / date / result cells
    form_cells = [t.get_text(strip=True) for t in soup.find_all(class_="FormHeading")]

    if len(form_cells) >= 1:
        result["stadium"]  = form_cells[0]
    if len(form_cells) >= 2:
        result["location"] = form_cells[1]
    if len(form_cells) >= 3:
        result["date"]     = form_cells[2]

    # Result is the FormHeading cell that contains won / draw / tied
    for cell in form_cells:
        if COMPLETED_RE.search(cell):
            result["match_result"] = cell
            break

    # ── Top scorer: scan all batting tables ────────────────────────────────────
    # Batting tables are identified by having a "Batsman" or "R" column header
    # class="TableHeadingLight" marks header cells; class="TableCell" marks data cells
    best_name, best_runs = "N/A", -1

    for table in soup.find_all("table"):
        headers = [th.get_text(strip=True) for th in table.find_all(class_="TableHeadingLight")]
        if "R" not in headers:
            continue                        # not a batting table

        r_idx = headers.index("R")         # column index of "Runs"

        for row in table.find_all("tr"):
            cols = row.find_all(class_="TableCell")
            if len(cols) <= r_idx:
                continue

            player = cols[0].get_text(strip=True)

            # Skip non-player rows: Extras, Total, DNB, FOW …
            if SKIP_ROW.match(player) or cols[0].find("b"):
                continue

            runs_str = cols[r_idx].get_text(strip=True).replace("*", "").strip()
            if not runs_str.isdigit():
                continue

            runs = int(runs_str)
            if runs > best_runs:
                best_runs = runs
                best_name = player

    if best_runs >= 0:
        result["top_scorer"] = best_name
        result["top_runs"]   = best_runs

    return result


# ── Step 3: Build CSV ──────────────────────────────────────────────────────────

def scrape(country_code: str, country_name: str) -> list[dict]:
    log.info("")
    log.info("=" * 55)
    log.info("  %s (%s)", country_name, country_code)
    log.info("=" * 55)

    matches = get_match_list(country_code)
    rows = []

    for i, m in enumerate(matches, 1):
        log.info("  [%d/10] MatchCode=%s  %s", i, m["code"], m["date"])
        sc_data = parse_scorecard(m["code"])
        log.info("         %s v %s | %s | Top: %s (%s)",
                 sc_data["team1"], sc_data["team2"],
                 sc_data["match_result"][:35],
                 sc_data["top_scorer"], sc_data["top_runs"])

        rows.append({
            "Sl No.":         i,
            "Match Date":     sc_data["date"] or m["date"],
            "Team 1":         sc_data["team1"],
            "Team 2":         sc_data["team2"],
            "Stadium Name":   sc_data["stadium"],
            "Stadium Location": sc_data["location"],
            "Match Result":   sc_data["match_result"],
            "Top Scorer Name": sc_data["top_scorer"],
            "Top Scorer Runs": sc_data["top_runs"],
        })

    return rows


def main():
    all_rows = []
    for code, name in COUNTRIES.items():
        all_rows.extend(scrape(code, name))

    df = pd.DataFrame(all_rows, columns=[
        "Sl No.", "Match Date", "Team 1", "Team 2",
        "Stadium Name", "Stadium Location",
        "Match Result", "Top Scorer Name", "Top Scorer Runs",
    ])
    df.to_csv("match_data.csv", index=False, encoding="utf-8-sig")
    log.info("")
    log.info("✅  match_data.csv saved — %d rows", len(df))
    print("\n", df.to_string(index=False))


if __name__ == "__main__":
    main()