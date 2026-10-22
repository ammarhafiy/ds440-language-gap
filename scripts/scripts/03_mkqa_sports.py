"""
Step 3: pick out the sports questions from MKQA (Longpre et al., 2021).

First download MKQA from
    https://github.com/apple/ml-mkqa/raw/main/dataset/mkqa.jsonl.gz
and save it as data/raw/mkqa.jsonl.gz (do not unzip it). Then run:
    python scripts/03_mkqa_sports.py

Writes data/questions/mkqa_sports_candidates.csv.

The keyword search finds sports questions automatically, but it also catches some
false matches (for example a TV show called "Basketball Wives"). Open the CSV in
Excel or Google Sheets and fill in the "keep" column with yes or no for every row:
  - no  if the question is not really about sports
  - no  if the answer changes over time (rows marked maybe_time_sensitive = yes
        need a careful look, e.g. "who won the last ...", "how many titles ...")
  - yes otherwise
MKQA's answers date from around 2018-2019, so anything that could have changed
since then should be removed.
"""
import csv
import gzip
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
IN_PATH = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data" / "raw" / "mkqa.jsonl.gz"
OUT_PATH = ROOT / "data" / "questions" / "mkqa_sports_candidates.csv"

SPORTS_WORDS = [
    "nba", "basketball", "nfl", "football", "soccer", "fifa", "world cup", "olympic",
    "olympics", "super bowl", "mlb", "baseball", "world series", "nhl", "hockey",
    "stanley cup", "premier league", "la liga", "serie a", "bundesliga",
    "champions league", "uefa", "tennis", "wimbledon", "grand slam", "golf", "pga",
    "cricket", "rugby", "boxing", "ufc", "wwe", "wrestling", "formula one", "formula 1",
    "f1", "nascar", "marathon", "athlete", "quarterback", "pitcher", "playoffs",
    "mvp", "coach", "stadium", "badminton", "volleyball", "cycling", "tour de france",
]
SPORTS_RE = re.compile(r"\b(" + "|".join(re.escape(w) for w in SPORTS_WORDS) + r")\b")

# Words that often mean the answer can change over time. Rows with these are only
# flagged for your review, not removed.
TIME_RE = re.compile(
    r"\b(last|latest|current|currently|now|today|this year|this season|next|recent|"
    r"recently|most recent|so far|still|right now|as of|how many|most|record|leading)\b")

# Answer types that cannot be checked automatically are skipped.
SKIP_TYPES = {"unanswerable", "long_answer", "binary"}

COLUMNS = ["example_id", "question_en", "question_ms", "answer_type", "answer_en", "answer_ms",
           "accepted_answers_en", "accepted_answers_ms", "matched_word", "maybe_time_sensitive",
           "keep"]


def answer_texts(answers):
    """First answer text, plus every answer text and alias, for one language."""
    texts = []
    for a in answers or []:
        texts.append(a.get("text") or "")
        texts.extend(a.get("aliases") or [])
    texts = [t for t in dict.fromkeys(t.strip() for t in texts) if t]
    return (texts[0] if texts else ""), texts


def main():
    if not IN_PATH.exists():
        sys.exit(f"Missing file: {IN_PATH}\nDownload mkqa.jsonl.gz first (see the top of this script).")

    rows, total = [], 0
    with gzip.open(IN_PATH, "rt", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            total += 1
            example = json.loads(line)
            queries = example.get("queries", {})
            question_en = queries.get("en") or example.get("query", "")
            question_ms = queries.get("ms", "")
            answers_en = example.get("answers", {}).get("en", [])
            answers_ms = example.get("answers", {}).get("ms", [])
            answer_type = answers_en[0].get("type", "") if answers_en else ""

            match = SPORTS_RE.search(question_en.lower())
            if not match or not question_ms or answer_type in SKIP_TYPES:
                continue
            answer_en, accepted_en = answer_texts(answers_en)
            answer_ms, accepted_ms = answer_texts(answers_ms)
            if not answer_en:
                continue

            rows.append({
                "example_id": example.get("example_id", ""),
                "question_en": question_en,
                "question_ms": question_ms,
                "answer_type": answer_type,
                "answer_en": answer_en,
                "answer_ms": answer_ms or answer_en,
                "accepted_answers_en": "|".join(accepted_en),
                "accepted_answers_ms": "|".join(accepted_ms),
                "matched_word": match.group(1),
                "maybe_time_sensitive": "yes" if TIME_RE.search(question_en.lower()) else "no",
                "keep": "",
            })

    # Never overwrite a file that has already been reviewed (keep column filled in):
    # write the new candidate list next to it instead, so the two can be compared.
    out_path = OUT_PATH
    if OUT_PATH.exists():
        with open(OUT_PATH, newline="", encoding="utf-8-sig") as f:
            reviewed = any((r.get("keep") or "").strip() for r in csv.DictReader(f))
        if reviewed:
            out_path = OUT_PATH.with_name("mkqa_sports_candidates_new.csv")
            print(f"NOTE: {OUT_PATH.name} has already been reviewed, so it is not overwritten.")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    flagged = sum(r["maybe_time_sensitive"] == "yes" for r in rows)
    print(f"Read {total} MKQA questions; {len(rows)} look like sports questions "
          f"({flagged} flagged as maybe time-sensitive).")
    print(f"Saved to {out_path}")
    if out_path == OUT_PATH:
        print('Next: open the file and fill in the "keep" column with yes or no for each row.')


if __name__ == "__main__":
    main()
