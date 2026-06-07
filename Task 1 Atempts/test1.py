import requests

url = "https://www.howstat.com/Cricket/Statistics/Matches/MatchListCountry.asp?A=ENG&B=XXX&C=XXX"

r = requests.get(
    url,
    headers={
        "User-Agent": "Mozilla/5.0"
    },
    timeout=30,
)

print("STATUS:", r.status_code)
print("FINAL URL:", r.url)

with open("response.html", "w", encoding="utf-8") as f:
    f.write(r.text)

print(r.text[:2000])