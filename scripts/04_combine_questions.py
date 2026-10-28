"""
Step 4: combine the Wikidata and MKQA questions into one final question set,
then write every prompt that will be sent to the chatbots.

Run after 02_build_questions.py and after the MKQA review (keep column filled in).
If the MKQA file has a final_keep column (the result of the re-check), it is used
instead of keep.
    python scripts/04_combine_questions.py

Reads:
    data/questions/questions_v1.csv            Wikidata questions (from script 02)
    data/questions/mkqa_sports_candidates.csv  MKQA candidates with keep / final_keep = yes / no
    data/mkqa_answer_fixes.csv                 wrong or too-general MKQA answers to remove
    data/prompt_templates.csv                  prompt instruction and labels (English + Malay)
Writes:
    data/questions/questions_final.csv         one row per question (English + Malay)
    data/prompts/prompts.csv                   one row per prompt sent to a chatbot

Prompts:
    Wikidata questions: English + Malay x no facts + with facts   = 4 prompts per question
    MKQA questions:     English + Malay x no facts only          = 2 prompts per question
    (MKQA has no fact sentences, and MKQA questions are only used for Hypothesis 1,
     which compares English and Malay without facts.)
"""
import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
WIKIDATA_PATH = DATA / "questions" / "questions_v1.csv"
MKQA_PATH = DATA / "questions" / "mkqa_sports_candidates.csv"
FIXES_PATH = DATA / "mkqa_answer_fixes.csv"
PROMPT_TEMPLATES_PATH = DATA / "prompt_templates.csv"
QUESTIONS_OUT = DATA / "questions" / "questions_final.csv"
PROMPTS_OUT = DATA / "prompts" / "prompts.csv"

QUESTION_COLUMNS = [
    "question_id", "source", "league", "entity_type", "entity_qid", "template_id", "property",
    "answer_type", "question_en", "question_ms", "fact_en", "fact_ms", "answer_en", "answer_ms",
    "accepted_answers", "sitelinks", "has_malay_wikipedia", "source_id",
]
PROMPT_COLUMNS = ["prompt_id", "question_id", "source", "league", "language", "condition", "prompt"]

# Scoring lowercases replies, so 1-2 letter aliases such as "IN" (India), "US" or "LA" would match
# everyday words ("in", "us", Malay "la"). They are dropped, except these common abbreviations.
SHORT_OK = {"KL", "PJ", "JB", "NY", "NJ", "SF"}
# Short aliases that are also everyday English or Malay words (they would match almost any reply).
COMMON_WORDS = {"can", "bar", "may", "man", "son", "van", "pin", "tan", "ban"}


def read_csv(path):
    if not path.exists():
        sys.exit(f"Missing file: {path}")
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path, columns, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def split(value):
    return [v.strip() for v in (value or "").split("|") if v.strip()]


def usable_alias(alias):
    """Drop aliases that would make automatic scoring unreliable:
    - no letters or digits (e.g. flag emojis)
    - 1-2 characters, except the abbreviations in SHORT_OK (drops 'IN', 'US', 'ke', 'de', 'fr')
    - short everyday words such as 'can' (alias of Canada)"""
    if not re.search(r"\w", alias):
        return False
    if re.fullmatch(r"\d+(\.\d+)?", alias):      # numbers such as 82, 6.0 or 29.5 are always kept
        return True
    if len(alias) <= 2 and alias not in SHORT_OK:
        return False
    if alias.lower() in COMMON_WORDS:
        return False
    return True


def clean_answers(answers, remove=()):
    """Remove unusable or listed answers and duplicates (ignoring case), keeping the order."""
    remove = {r.lower() for r in remove}
    seen, kept = set(), []
    for a in answers:
        key = a.lower()
        if key in seen or key in remove or not usable_alias(a):
            continue
        seen.add(key)
        kept.append(a)
    return kept


def year_type(prop):
    return "year" if prop in ("birth_year", "founded_year") else "place"


def wikidata_rows():
    rows = []
    for q in read_csv(WIKIDATA_PATH):
        accepted = clean_answers(split(q["accepted_answers"]))
        if not accepted:
            accepted = [q["answer_en"]]
        rows.append({
            "question_id": q["question_id"],
            "source": "wikidata",
            "league": q["league"],
            "entity_type": q["entity_type"],
            "entity_qid": q["entity_qid"],
            "template_id": q["template_id"],
            "property": q["property"],
            "answer_type": year_type(q["property"]),
            "question_en": q["question_en"],
            "question_ms": q["question_ms"],
            "fact_en": q["fact_en"],
            "fact_ms": q["fact_ms"],
            "answer_en": q["answer_en"],
            "answer_ms": q["answer_ms"],
            "accepted_answers": "|".join(accepted),
            "sitelinks": q["sitelinks"],
            "has_malay_wikipedia": q["has_malay_wikipedia"],
            "source_id": q["entity_qid"],
        })
    return rows


def mkqa_rows():
    fixes = {}
    for f in read_csv(FIXES_PATH):
        fixes.setdefault(f["example_id"].strip(), []).append(f["remove_answer"].strip())

    candidates = read_csv(MKQA_PATH)
    if "keep" not in candidates[0]:
        sys.exit("The MKQA file has no 'keep' column. Run script 03 and review the questions first.")
    # final_keep = the decision after the re-check; keep = the first-pass review
    decision = "final_keep" if "final_keep" in candidates[0] else "keep"
    unreviewed = [c for c in candidates if c[decision].strip().lower() not in ("yes", "no")]
    if unreviewed:
        print(f"NOTE: {len(unreviewed)} MKQA rows have no yes/no in the {decision} column; they are left out.")

    rows = []
    for c in candidates:
        if c[decision].strip().lower() != "yes":
            continue
        accepted = split(c["accepted_answers_en"]) + split(c["accepted_answers_ms"])
        # For date answers, also accept the year on its own, unless the year is already in the
        # question (e.g. "when does the season start 2018"), where it would give the answer away.
        if c["answer_type"] == "date":
            for a in list(accepted):
                year = re.match(r"^(\d{4})-\d{2}-\d{2}$", a)
                if year and year.group(1) not in c["question_en"]:
                    accepted.append(year.group(1))
        accepted = clean_answers(accepted, remove=fixes.get(c["example_id"].strip(), []))
        rows.append({
            "question_id": f"mkqa-{c['example_id'].strip()}",
            "source": "mkqa",
            "league": "mixed",
            "entity_type": "",
            "entity_qid": "",
            "template_id": "",
            "property": "",
            "answer_type": c["answer_type"],
            "question_en": c["question_en"],
            "question_ms": c["question_ms"],
            "fact_en": "",
            "fact_ms": "",
            "answer_en": c["answer_en"],
            "answer_ms": c["answer_ms"],
            "accepted_answers": "|".join(accepted),
            "sitelinks": "",
            "has_malay_wikipedia": "",
            "source_id": c["example_id"].strip(),
        })
    return rows


def build_prompt(template, question, fact=None):
    lines = [template["instruction"].strip(), ""]
    if fact is not None:
        lines.append(f"{template['fact_label'].strip()} {fact}")
    lines.append(f"{template['question_label'].strip()} {question}")
    return "\n".join(lines)


def prompt_rows(questions):
    templates = {t["language"].strip(): t for t in read_csv(PROMPT_TEMPLATES_PATH)}
    missing = [lang for lang in ("en", "ms") if not templates.get(lang, {}).get("instruction", "").strip()]
    if missing:
        print("\nSTOPPED before writing prompts: the instruction is empty for language(s): "
              + ", ".join(missing))
        print("Fill in the 'instruction' column in data/prompt_templates.csv, then run this script again.")
        return None

    rows = []
    for q in questions:
        conditions = ["no_facts", "with_facts"] if q["source"] == "wikidata" else ["no_facts"]
        for lang in ("en", "ms"):
            question = q[f"question_{lang}"]
            if not question:
                sys.exit(f"Question {q['question_id']} has no {lang} text.")
            for condition in conditions:
                fact = q[f"fact_{lang}"] if condition == "with_facts" else None
                rows.append({
                    "prompt_id": f"{q['question_id']}-{lang}-{condition}",
                    "question_id": q["question_id"],
                    "source": q["source"],
                    "league": q["league"],
                    "language": lang,
                    "condition": condition,
                    "prompt": build_prompt(templates[lang], question, fact),
                })
    return rows


def main():
    wikidata = wikidata_rows()
    mkqa = mkqa_rows()
    questions = wikidata + mkqa
    ids = [q["question_id"] for q in questions]
    if len(ids) != len(set(ids)):
        sys.exit("Duplicate question IDs found; check the input files.")

    write_csv(QUESTIONS_OUT, QUESTION_COLUMNS, questions)
    print(f"Saved {len(questions)} questions to {QUESTIONS_OUT}")
    for league in ("msl", "nba", "mixed"):
        print(f"  {league}: {sum(q['league'] == league for q in questions)}")

    prompts = prompt_rows(questions)
    if prompts is None:
        return
    write_csv(PROMPTS_OUT, PROMPT_COLUMNS, prompts)
    print(f"\nSaved {len(prompts)} prompts to {PROMPTS_OUT}")
    print(f"  Wikidata: {len(wikidata)} questions x 4 = {len(wikidata) * 4}")
    print(f"  MKQA:     {len(mkqa)} questions x 2 = {len(mkqa) * 2}")


if __name__ == "__main__":
    main()
