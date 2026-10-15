"""
Step 1: download NBA and Malaysia Super League players and clubs from Wikidata.

Run from the repository folder:
    python scripts/01_get_wikidata.py

Outputs (all in data/raw/):
    players_msl.csv, players_nba.csv   one row per player
    clubs_msl.csv,   clubs_nba.csv     one row per club
    places.csv                         English and Malay names, plus other accepted
                                       names, for every birthplace, home city and stadium
    download_info.txt                  the date the data was downloaded

Only clubs that have a home venue (P115) are used. This leaves out Wikidata items
that are not real teams, such as season pages that also list the NBA as their
league (see queries/README.md).
"""
import csv
import sys
import time
from datetime import date
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"

ENDPOINT = "https://query.wikidata.org/sparql"
HEADERS = {
    # Wikidata asks every script to identify itself.
    "User-Agent": "DS440-language-gap/0.1 (https://github.com/ammarhafiy/ds440-language-gap)",
    "Accept": "application/sparql-results+json",
}

# Short code used in file names -> league name exactly as written on Wikidata.
LEAGUES = {
    "msl": "Malaysia Super League",
    "nba": "National Basketball Association",
}

ENTITY_PREFIX = "http://www.wikidata.org/entity/"
PLACES_PER_QUERY = 200  # how many places to look up in one query

# hint:Query hint:optimizer "None" makes Wikidata run the lines in the order
# they are written: find the league first, then its clubs, then their players.
# Without it, the server sometimes starts from all of Wikidata and times out.
PLAYERS_QUERY = """
SELECT DISTINCT ?player ?nameEn ?nameMs ?links ?msArticle ?birthplace ?dob WHERE {
  hint:Query hint:optimizer "None" .
  ?league rdfs:label "__LEAGUE__"@en .
  ?club wdt:P118 ?league ; wdt:P115 ?venue .
  ?player wdt:P54 ?club ; wdt:P31 wd:Q5 ; wikibase:sitelinks ?links .
  OPTIONAL { ?player rdfs:label ?nameEn . FILTER(LANG(?nameEn) = "en") }
  OPTIONAL { ?player rdfs:label ?nameMs . FILTER(LANG(?nameMs) = "ms") }
  OPTIONAL { ?msArticle schema:about ?player ;
                        schema:isPartOf <https://ms.wikipedia.org/> . }
  OPTIONAL { ?player wdt:P19 ?birthplace . }
  OPTIONAL { ?player wdt:P569 ?dob . }
}
"""

CLUBS_QUERY = """
SELECT DISTINCT ?club ?nameEn ?nameMs ?venue ?hq ?admin ?inception WHERE {
  hint:Query hint:optimizer "None" .
  ?league rdfs:label "__LEAGUE__"@en .
  ?club wdt:P118 ?league ; wdt:P115 ?venue .
  OPTIONAL { ?club rdfs:label ?nameEn . FILTER(LANG(?nameEn) = "en") }
  OPTIONAL { ?club rdfs:label ?nameMs . FILTER(LANG(?nameMs) = "ms") }
  OPTIONAL { ?club wdt:P159 ?hq . }
  OPTIONAL { ?club wdt:P131 ?admin . }
  OPTIONAL { ?club wdt:P571 ?inception . }
}
"""

PLACES_QUERY = """
SELECT ?place ?text ?kind WHERE {
  VALUES ?place { __VALUES__ }
  { ?place rdfs:label ?text . BIND("label" AS ?kind) }
  UNION
  { ?place skos:altLabel ?text . BIND("alias" AS ?kind) }
  FILTER(LANG(?text) = "en" || LANG(?text) = "ms")
}
"""


def run_query(query, retries=4):
    """Send one SPARQL query to Wikidata and return the result rows."""
    for attempt in range(1, retries + 1):
        try:
            response = requests.post(ENDPOINT, data={"query": query},
                                     headers=HEADERS, timeout=120)
            if response.status_code == 429:  # too many requests: wait and retry
                wait = int(response.headers.get("Retry-After", 30))
                print(f"  Wikidata asked us to slow down, waiting {wait} s ...")
                time.sleep(wait)
                continue
            response.raise_for_status()
            return response.json()["results"]["bindings"]
        except (requests.RequestException, ValueError, KeyError) as error:
            print(f"  Query failed (attempt {attempt}/{retries}): {error}")
            time.sleep(15 * attempt)
    sys.exit("Wikidata kept failing. Wait a few minutes, then run this script again.")


def get_qid(row, key):
    """Return the Q-number in a result cell, or '' if the cell is empty or not an item."""
    value = row.get(key, {}).get("value", "")
    return value[len(ENTITY_PREFIX):] if value.startswith(ENTITY_PREFIX) else ""


def get_text(row, key):
    return row.get(key, {}).get("value", "")


def get_year(value):
    """'1984-12-30T00:00:00Z' -> '1984'. Returns '' for empty or unusual dates."""
    if not value or value.startswith("-"):
        return ""
    year = value[:4]
    return year if year.isdigit() else ""


def join(values):
    return "|".join(sorted(values))


def collect_players(league_name):
    rows = run_query(PLAYERS_QUERY.replace("__LEAGUE__", league_name))
    players = {}
    for row in rows:
        player_qid = get_qid(row, "player")
        if not player_qid:
            continue
        p = players.setdefault(player_qid, {
            "player_qid": player_qid, "name_en": "", "name_ms": "",
            "sitelinks": 0, "has_malay_wikipedia": 0,
            "birthplace_qids": set(), "birth_years": set(),
        })
        p["name_en"] = p["name_en"] or get_text(row, "nameEn")
        p["name_ms"] = p["name_ms"] or get_text(row, "nameMs")
        if get_text(row, "links").isdigit():
            p["sitelinks"] = int(get_text(row, "links"))
        if get_text(row, "msArticle"):
            p["has_malay_wikipedia"] = 1
        if get_qid(row, "birthplace"):
            p["birthplace_qids"].add(get_qid(row, "birthplace"))
        if get_year(get_text(row, "dob")):
            p["birth_years"].add(get_year(get_text(row, "dob")))
    return players


def collect_clubs(league_name):
    rows = run_query(CLUBS_QUERY.replace("__LEAGUE__", league_name))
    clubs = {}
    for row in rows:
        club_qid = get_qid(row, "club")
        if not club_qid:
            continue
        c = clubs.setdefault(club_qid, {
            "club_qid": club_qid, "name_en": "", "name_ms": "",
            "venue_qids": set(), "hq_qids": set(), "admin_qids": set(),
            "founded_years": set(),
        })
        c["name_en"] = c["name_en"] or get_text(row, "nameEn")
        c["name_ms"] = c["name_ms"] or get_text(row, "nameMs")
        for key, field in (("venue", "venue_qids"), ("hq", "hq_qids"), ("admin", "admin_qids")):
            if get_qid(row, key):
                c[field].add(get_qid(row, key))
        if get_year(get_text(row, "inception")):
            c["founded_years"].add(get_year(get_text(row, "inception")))
    return clubs


def collect_places(place_qids):
    """Look up English and Malay names and other accepted names for each place."""
    places = {q: {"place_qid": q, "label_en": "", "label_ms": "",
                  "aliases_en": set(), "aliases_ms": set()} for q in place_qids}
    qids = sorted(place_qids)
    for start in range(0, len(qids), PLACES_PER_QUERY):
        chunk = qids[start:start + PLACES_PER_QUERY]
        print(f"  places {start + 1}-{start + len(chunk)} of {len(qids)}")
        values = " ".join("wd:" + q for q in chunk)
        for row in run_query(PLACES_QUERY.replace("__VALUES__", values)):
            place = places.get(get_qid(row, "place"))
            lang = row.get("text", {}).get("xml:lang", "")
            text = get_text(row, "text")
            if place is None or lang not in ("en", "ms") or not text:
                continue
            if get_text(row, "kind") == "label":
                place["label_" + lang] = text
            else:
                place["aliases_" + lang].add(text)
        time.sleep(1)
    return places


def write_csv(path, rows, columns):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: join(v) if isinstance(v, set) else v for k, v in row.items()})


def main():
    all_place_qids = set()
    for code, league_name in LEAGUES.items():
        print(f"\n{league_name}")

        print("  downloading players ...")
        players = collect_players(league_name)
        write_csv(RAW_DIR / f"players_{code}.csv",
                  sorted(players.values(), key=lambda p: p["player_qid"]),
                  ["player_qid", "name_en", "name_ms", "sitelinks", "has_malay_wikipedia",
                   "birthplace_qids", "birth_years"])
        time.sleep(1)

        print("  downloading clubs ...")
        clubs = collect_clubs(league_name)
        write_csv(RAW_DIR / f"clubs_{code}.csv",
                  sorted(clubs.values(), key=lambda c: c["club_qid"]),
                  ["club_qid", "name_en", "name_ms", "venue_qids", "hq_qids",
                   "admin_qids", "founded_years"])
        time.sleep(1)

        for p in players.values():
            all_place_qids |= p["birthplace_qids"]
        for c in clubs.values():
            all_place_qids |= c["venue_qids"] | c["hq_qids"] | c["admin_qids"]

        one_place = sum(len(p["birthplace_qids"]) == 1 for p in players.values())
        one_year = sum(len(p["birth_years"]) == 1 for p in players.values())
        print(f"  {len(players)} players ({one_place} with one birthplace, "
              f"{one_year} with one birth year), {len(clubs)} clubs")
        if not players:
            print(f"  WARNING: no players found. Check that '{league_name}' is the exact "
                  "English name of the league on Wikidata. If it is, try deleting the "
                  "'hint:Query hint:optimizer' lines in the queries and run again.")

    print("\nDownloading place names ...")
    places = collect_places(all_place_qids)
    write_csv(RAW_DIR / "places.csv",
              sorted(places.values(), key=lambda p: p["place_qid"]),
              ["place_qid", "label_en", "label_ms", "aliases_en", "aliases_ms"])

    (RAW_DIR / "download_info.txt").write_text(
        f"Downloaded from the Wikidata Query Service on {date.today().isoformat()}.\n",
        encoding="utf-8")
    print(f"\nDone. Files saved in {RAW_DIR}")


if __name__ == "__main__":
    main()
