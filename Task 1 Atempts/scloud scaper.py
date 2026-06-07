import cloudscraper

url = "https://www.howstat.com/Cricket/Statistics/Matches/MatchListCountry.asp?A=ENG&B=XXX&C=XXX"

scraper = cloudscraper.create_scraper()

r = scraper.get(url)

print("STATUS:", r.status_code)
print(r.text[:1000])