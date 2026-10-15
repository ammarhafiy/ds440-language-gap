"""
Step 2: build the question set from the Wikidata downloads.

Run after 01_get_wikidata.py:
    python scripts/02_build_questions.py

Reads:
    data/templates.csv     question and fact templates (English + Malay)
    data/league_terms.csv  words used for each league (e.g. "footballer")
    data/raw/*.csv         files made by 01_get_wikidata.py
Writes:
    data/questions/questions_v1.csv

Players: a random sample of PLAYERS_PER_LEAGUE players per league (fixed seed,
so the same players are picked every time). Clubs: every club is used.
A question is only made when Wikidata has exactly one answer for it.
"""
import csv
import random
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
OUT_PATH = DATA_DIR / "questions" / "questions_v1.csv"

SEED = 440                 # fixed random seed: change it only if you want a new sample
PLAYERS_PER_LEAGUE = 500
LEAGUES = ["msl", "nba"]

OUT_COLUMNS = [
    "question_id", "league", "entity_type", "entity_qid", "entity_name_en", "entity_name_ms",
    "template_id", "property", "question_en", "question_ms", "fact_en", "fact_ms",
    "answer_en", "answer_ms", "accepted_answers", "sitelinks", "has_malay_wikipedia",
]


def read_csv(path):
    if not path.exists():
        sys.exit(f"Missing file: {path}\nRun scripts/01_get_wikidata.py first.")
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def split(value):
    return [v for v in (value or "").split("|") if v]


def unique(values):
    """Remove blanks and duplicates (ignoring upper/lower case), keeping the order."""
    seen, result = set(), []
    for v in values:
        key = v.strip().lower()
        if key and key not in seen:
            seen.add(key)
            result.append(v.strip())
    return result


def fill(template, **values):
    """Replace {name}, {desc} and {answer}, then start the sentence with a capital letter
    (Malay sentences that begin with {desc} would otherwise start in lower case)."""
    for key, value in values.items():
        template = template.replace("{" + key + "}", value)
    return template[:1].upper() + template[1:]


def has_real_name(name):
    """Skip items whose 'name' is missing or just a Q-number."""
    return bool(name) and not (name[0] == "Q" and name[1:].isdigit())


def place_answer(places, place_qid):
    """(answer_en, answer_ms, accepted names) for a place, or None if it has no English name."""
    place = places.get(place_qid)
    if not place or not place["label_en"]:
        return None
    answer_en = place["label_en"]
    answer_ms = place["label_ms"] or answer_en
    accepted = unique([answer_en, answer_ms] + split(place["aliases_en"]) + split(place["aliases_ms"]))
    return answer_en, answer_ms, accepted


def single(values):
    """Return the only value in a list, or None if there are zero or several."""
    return values[0] if len(values) == 1 else None


def get_fact(entity, prop, places):
    """Return (answer_en, answer_ms, accepted names) or None if there isn't exactly one answer."""
    if prop == "birthplace":
        q = single(split(entity["birthplace_qids"]))
        return place_answer(places, q) if q else None
    if prop == "birth_year":
        year = single(split(entity["birth_years"]))
        return (year, year, [year]) if year else None
    if prop == "home_city":
        q = single(split(entity["hq_qids"]) or split(entity["admin_qids"]))
        return place_answer(places, q) if q else None
    if prop == "founded_year":
        year = single(split(entity["founded_years"]))
        return (year, year, [year]) if year else None
    if prop == "stadium":
        q = single(split(entity["venue_qids"]))
        return place_answer(places, q) if q else None
    sys.exit(f"Unknown property in data/templates.csv: {prop}")


def make_row(league, entity_type, entity_qid, entity, template, terms, fact, warnings):
    answer_en, answer_ms, accepted = fact
    name_en = entity["name_en"]
    name_ms = entity["name_ms"] or name_en      # most names are the same in Malay
    desc_en = terms[f"{entity_type}_desc_en"]
    desc_ms = terms[f"{entity_type}_desc_ms"]

    question_ms = fact_ms = ""
    malay_ready = template["question_ms"] and template["fact_ms"] and (
        desc_ms or "{desc}" not in template["question_ms"] + template["fact_ms"])
    if malay_ready:
        question_ms = fill(template["question_ms"], name=name_ms, desc=desc_ms, answer=answer_ms)
        fact_ms = fill(template["fact_ms"], name=name_ms, desc=desc_ms, answer=answer_ms)
    else:
        warnings.add(template["template_id"])

    return {
        "question_id": f"{league}-{entity_qid}-{template['template_id']}",
        "league": league,
        "entity_type": entity_type,
        "entity_qid": entity_qid,
        "entity_name_en": name_en,
        "entity_name_ms": name_ms,
        "template_id": template["template_id"],
        "property": template["property"],
        "question_en": fill(template["question_en"], name=name_en, desc=desc_en, answer=answer_en),
        "question_ms": question_ms,
        "fact_en": fill(template["fact_en"], name=name_en, desc=desc_en, answer=answer_en),
        "fact_ms": fact_ms,
        "answer_en": answer_en,
        "answer_ms": answer_ms,
        "accepted_answers": "|".join(accepted),
        "sitelinks": entity.get("sitelinks", ""),
        "has_malay_wikipedia": entity.get("has_malay_wikipedia", ""),
    }


def main():
    templates = [t for t in read_csv(DATA_DIR / "templates.csv") if t["use"].strip().lower() == "yes"]
    terms_by_league = {r["league"]: r for r in read_csv(DATA_DIR / "league_terms.csv")}
    places = {r["place_qid"]: r for r in read_csv(RAW_DIR / "places.csv")}
    player_templates = [t for t in templates if t["entity_type"] == "player"]
    club_templates = [t for t in templates if t["entity_type"] == "club"]

    rows, warnings = [], set()
    rng = random.Random(SEED)

    for league in LEAGUES:
        terms = terms_by_league[league]

        # Players: keep those with a real name and at least one usable fact, then sample.
        players = [p for p in read_csv(RAW_DIR / f"players_{league}.csv") if has_real_name(p["name_en"])]
        eligible = [p for p in players
                    if any(get_fact(p, t["property"], places) for t in player_templates)]
        eligible.sort(key=lambda p: p["player_qid"])   # same order every run, so the sample repeats
        sample = rng.sample(eligible, min(PLAYERS_PER_LEAGUE, len(eligible)))
        print(f"{league}: {len(players)} players, {len(eligible)} usable, {len(sample)} sampled")
        if len(eligible) < PLAYERS_PER_LEAGUE:
            print(f"  NOTE: fewer than {PLAYERS_PER_LEAGUE} usable players, so all of them are used.")

        for p in sample:
            for t in player_templates:
                fact = get_fact(p, t["property"], places)
                if fact:
                    rows.append(make_row(league, "player", p["player_qid"], p, t, terms, fact, warnings))

        # Clubs: use every club with a real name.
        for c in read_csv(RAW_DIR / f"clubs_{league}.csv"):
            if not has_real_name(c["name_en"]):
                continue
            for t in club_templates:
                fact = get_fact(c, t["property"], places)
                if fact:
                    rows.append(make_row(league, "club", c["club_qid"], c, t, terms, fact, warnings))

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=OUT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nSaved {len(rows)} questions to {OUT_PATH}")
    counts = Counter((r["league"], r["template_id"]) for r in rows)
    for (league, template_id), n in sorted(counts.items()):
        print(f"  {league}  {template_id}: {n}")
    if warnings:
        print("\nNOTE: Malay questions are empty for templates " + ", ".join(sorted(warnings)) + ".")
        print("Add your Malay translations to question_ms and fact_ms in data/templates.csv,")
        print("and to player_desc_ms and club_desc_ms in data/league_terms.csv, then run this again.")


if __name__ == "__main__":
    main()
