import os
import requests
from bs4 import BeautifulSoup

# Set your Atlassian credentials as environment variables for security
WIKI_URL = "https://trendmicro.atlassian.net/wiki/spaces/DSLABS/database/943660708"
USERNAME = os.environ.get("ATLASSIAN_USERNAME")
API_TOKEN = os.environ.get("ATLASSIAN_API_TOKEN")

def fetch_wiki_table():
    session = requests.Session()
    session.auth = (USERNAME, API_TOKEN)
    headers = {"Accept": "text/html"}
    response = session.get(WIKI_URL, headers=headers)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    # Find the table (adjust selector as needed)
    table = soup.find("table")
    return table

def parse_and_write_regex(table):
    rows = table.find_all("tr")
    headers = [th.get_text(strip=True) for th in rows[0].find_all("th")]
    tsl_idx = headers.index("tsl_id")
    regex_idx = headers.index("DV_filter_logic")
    for row in rows[1:]:
        cols = row.find_all("td")
        if len(cols) < max(tsl_idx, regex_idx) + 1:
            continue
        tsl_id = cols[tsl_idx].get_text(strip=True)
        regex = cols[regex_idx].get_text(strip=True)
        if tsl_id and regex:
            out_dir = os.path.join("report", "regex")
            os.makedirs(out_dir, exist_ok=True)
            out_path = os.path.join(out_dir, f"{tsl_id}.txt")
            with open(out_path, "w") as f:
                f.write(regex)
            print(f"Wrote regex for {tsl_id} to {out_path}")

if __name__ == "__main__":
    table = fetch_wiki_table()
    parse_and_write_regex(table)