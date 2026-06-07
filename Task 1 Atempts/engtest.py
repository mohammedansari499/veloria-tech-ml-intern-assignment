import cloudscraper
from bs4 import BeautifulSoup

url = "https://www.howstat.com/Cricket/Statistics/Matches/MatchListCountry.asp?A=ENG&B=XXX&C=XXX"

html = cloudscraper.create_scraper().get(url).text

with open("england.html", "w", encoding="utf-8") as f:
    f.write(html)

print("saved")