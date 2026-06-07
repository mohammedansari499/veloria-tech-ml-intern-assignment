import cloudscraper
from bs4 import BeautifulSoup

url = "https://www.howstat.com/Cricket/Statistics/Matches/MatchListCountry.asp?A=ENG&B=XXX&C=XXX"

scraper = cloudscraper.create_scraper()

html = scraper.get(url).text

soup = BeautifulSoup(html, "html.parser")

tables = soup.find_all("table")

print("TABLES:", len(tables))

for i, table in enumerate(tables):

    rows = table.find_all("tr")

    if len(rows) < 5:
        continue

    print("\n" + "=" * 80)
    print("TABLE", i)
    print("ROWS:", len(rows))

    for row in rows[:5]:

        cells = [
            c.get_text(" ", strip=True)
            for c in row.find_all(["td", "th"])
        ]

        print(cells)