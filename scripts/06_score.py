"""
Step 6: score the chatbot replies automatically and make an accuracy table.

Run after 05_collect_responses.py:
    python scripts/06_score.py                       # score every file in data/responses/
    python scripts/06_score.py --files data/responses/gemini_gemini-3.1-flash-lite_pilot.csv

Reads:
    data/questions/questions_final.csv     accepted answers for every question
    data/responses/*.csv                   replies from script 05
Writes (one pair per responses file):
    data/scored/<name>_scored.csv          every reply with its score and flags
    results/accuracy_<name>.csv            accuracy per group with 95% Wilson confidence intervals

Scoring rules (see notes/scoring_rubric.md):
    1. The reply and every accepted answer are normalized: lowercase, accents removed,
       punctuation and Markdown (e.g. **bold**) removed, leading zeros removed from numbers.
    2. Correct (1) if the reply contains any accepted answer as a whole word or phrase.
       Numbers written as words are also recognized ("four" / "empat" = 4), and dates are
       matched in several formats ("6 September 2018", "September 6, 2018", ...).
       For MKQA answers with a unit (e.g. "3 minutes"), the number alone is also accepted.
    3. Incorrect (0) otherwise. Empty replies and refusals are flagged in the 'refusal' column.
    4. The language of each reply (en / ms / unknown) is guessed from common words.
Rows whose request failed (error column filled) are not scored.
"""
import argparse
import csv
import math
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
QUESTIONS_PATH = ROOT / "data" / "questions" / "questions_final.csv"
RESPONSES_DIR = ROOT / "data" / "responses"
SCORED_DIR = ROOT / "data" / "scored"
RESULTS_DIR = ROOT / "results"

GROUP_COLUMNS = ["source", "league", "language", "condition"]

# ---------- text normalization ----------

def normalize(text):
    """Lowercase, remove accents, punctuation and Markdown, and leading zeros in numbers."""
    text = unicodedata.normalize("NFKD", str(text).lower())
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r"[^\w\s]|_", " ", text)          # punctuation, *, #, etc. become spaces
    text = re.sub(r"\b0+(\d)", r"\1", text)          # 06 -> 6
    return re.sub(r"\s+", " ", text).strip()


# ---------- numbers written as words (English and Malay) ----------

UNITS = {
    # English
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
    "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13,
    "fourteen": 14, "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19,
    # Malay
    "kosong": 0, "sifar": 0, "satu": 1, "dua": 2, "tiga": 3, "empat": 4, "lima": 5, "enam": 6,
    "tujuh": 7, "lapan": 8, "sembilan": 9, "sepuluh": 10, "sebelas": 11,
}
TENS = {"twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70,
        "eighty": 80, "ninety": 90}
NUMBER_WORDS = set(UNITS) | set(TENS) | {"belas", "puluh", "hundred", "ratus", "seratus"}


def words_to_digits(text):
    """Replace runs of number words with digits, e.g. 'lapan puluh dua' -> '82'."""
    out, run = [], []

    def flush():
        if not run:
            return
        total, current = 0, 0
        for tok in run:
            if tok in UNITS:
                current += UNITS[tok]
            elif tok in TENS:
                current += TENS[tok]
            elif tok == "belas":                    # dua belas = 12
                current = (current or 1) + 10
            elif tok == "puluh":                    # lapan puluh = 80
                current = (current or 1) * 10
            elif tok in ("hundred", "ratus"):       # one hundred / lima ratus
                total += (current or 1) * 100
                current = 0
            elif tok == "seratus":                  # seratus = 100
                total += 100
        out.append(str(total + current))
        run.clear()

    for tok in text.split():
        if tok in NUMBER_WORDS:
            run.append(tok)
        else:
            flush()
            out.append(tok)
    flush()
    return " ".join(out)


# ---------- dates ----------

MONTHS_EN = ["january", "february", "march", "april", "may", "june", "july", "august",
             "september", "october", "november", "december"]
MONTHS_MS = ["januari", "februari", "mac", "april", "mei", "jun", "julai", "ogos",
             "september", "oktober", "november", "disember"]


def date_variants(answer):
    """For an answer like 2018-09-06, return other ways of writing the same date."""
    m = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", answer.strip())
    if not m:
        return []
    year, month, day = m.group(1), int(m.group(2)), int(m.group(3))
    if not 1 <= month <= 12:
        return []
    variants = []
    for months in (MONTHS_EN, MONTHS_MS):
        name = months[month - 1]
        variants += [f"{day} {name} {year}", f"{name} {day} {year}"]
    return variants


def number_alone(answer):
    """'3 minutes' -> '3' (MKQA answers with a unit)."""
    m = re.match(r"^\s*(\d+(?:\.\d+)?)\s+\D", answer)
    return [m.group(1)] if m else []


# ---------- refusals and reply language ----------

REFUSAL = re.compile(
    r"\b(i don ?t know|i do not know|not sure|i m not certain|i am not certain|unable to|"
    r"cannot (?:find|determine|provide)|can ?t (?:find|determine|provide)|no information|"
    r"not available|unknown|tidak tahu|tidak pasti|tiada maklumat|tidak dapat|maklumat tidak)\b")

MALAY_WORDS = {"di", "dan", "yang", "pada", "dilahirkan", "beliau", "ialah", "adalah", "dalam",
               "untuk", "tahun", "kelab", "pasukan", "pemain", "ini", "itu", "tidak", "saya",
               "dengan", "ke", "dari", "oleh", "telah", "bermula", "memenangi", "terdapat",
               "mesti", "berpangkalan", "berpusat", "diasaskan", "bandar", "negeri", "musim",
               "peringkat", "perlawanan", "mewakili", "jawapan", "ialah"}
ENGLISH_WORDS = {"the", "was", "born", "in", "is", "of", "and", "he", "she", "it", "team",
                 "year", "has", "have", "there", "are", "on", "with", "won", "by", "to", "you",
                 "founded", "based", "city", "club", "began", "season", "games", "stages",
                 "his", "her", "player", "answer"}


def reply_language(normalized_reply):
    words = normalized_reply.split()
    ms = sum(w in MALAY_WORDS for w in words)
    en = sum(w in ENGLISH_WORDS for w in words)
    if ms == en:
        return "unknown"            # e.g. only a name or a year
    return "ms" if ms > en else "en"


# ---------- scoring ----------

def accepted_forms(question):
    answers = [a for a in question["accepted_answers"].split("|") if a.strip()]
    extra = []
    for a in answers:
        extra += date_variants(a)
        if question["source"] == "mkqa" and question["answer_type"] == "number_with_unit":
            extra += number_alone(a)
    forms = {normalize(a) for a in answers + extra}
    return sorted(f for f in forms if f)


def score_reply(reply, forms):
    """Return (score, matched form). Whole-word / whole-phrase matching on normalized text."""
    norm = normalize(reply)
    texts = {f" {norm} ", f" {words_to_digits(norm)} "}
    for form in sorted(forms, key=len, reverse=True):
        if any(f" {form} " in t for t in texts):
            return 1, form
    return 0, ""


def wilson(correct, n, z=1.96):
    if n == 0:
        return "", ""
    p = correct / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return round(max(0.0, centre - half), 3), round(min(1.0, centre + half), 3)


def read_csv(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path, columns, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def score_file(path, questions):
    rows = read_csv(path)
    if not rows or "prompt_id" not in rows[0]:
        print(f"Skipping {path.name}: not a responses file.")
        return
    forms_cache = {}
    scored, skipped = [], 0
    for r in rows:
        q = questions.get(r["question_id"])
        if q is None:
            sys.exit(f"{path.name}: unknown question_id {r['question_id']}")
        out = dict(r)
        out["answer_en"] = q["answer_en"]
        out["answer_ms"] = q["answer_ms"]
        if r.get("error"):
            out.update(score="", matched_answer="", refusal="", reply_language="", language_match="")
            skipped += 1
        else:
            if r["question_id"] not in forms_cache:
                forms_cache[r["question_id"]] = accepted_forms(q)
            s, matched = score_reply(r["response"], forms_cache[r["question_id"]])
            norm = normalize(r["response"])
            lang = reply_language(norm)
            refusal = int(not norm or (s == 0 and bool(REFUSAL.search(norm))))
            out.update(score=s, matched_answer=matched, refusal=refusal, reply_language=lang,
                       language_match="" if lang == "unknown" else int(lang == r["language"]))
        scored.append(out)

    columns = list(rows[0].keys()) + ["answer_en", "answer_ms", "score", "matched_answer",
                                      "refusal", "reply_language", "language_match"]
    stem = path.stem
    scored_path = SCORED_DIR / f"{stem}_scored.csv"
    write_csv(scored_path, columns, scored)

    # accuracy per group
    groups = {}
    for r in scored:
        if r["score"] == "":
            continue
        key = tuple(r[c] for c in GROUP_COLUMNS)
        g = groups.setdefault(key, {"n": 0, "correct": 0, "refusals": 0})
        g["n"] += 1
        g["correct"] += int(r["score"])
        g["refusals"] += int(r["refusal"])
    table = []
    for key in sorted(groups):
        g = groups[key]
        low, high = wilson(g["correct"], g["n"])
        table.append(dict(zip(GROUP_COLUMNS, key), n=g["n"], correct=g["correct"],
                          accuracy=round(g["correct"] / g["n"], 3), ci_low=low, ci_high=high,
                          refusals=g["refusals"]))
    results_path = RESULTS_DIR / f"accuracy_{stem}.csv"
    write_csv(results_path, GROUP_COLUMNS + ["n", "correct", "accuracy", "ci_low", "ci_high", "refusals"], table)

    print(f"\n{path.name}: {len(scored) - skipped} replies scored, {skipped} failed requests skipped")
    print(f"  {'source':9} {'league':6} {'lang':4} {'condition':10} {'correct':>9}  accuracy  95% CI")
    for t in table:
        print(f"  {t['source']:9} {t['league']:6} {t['language']:4} {t['condition']:10} "
              f"{t['correct']:>4}/{t['n']:<4}  {t['accuracy']:.2f}      [{t['ci_low']:.2f}, {t['ci_high']:.2f}]")
    print(f"  Saved {scored_path.relative_to(ROOT)} and {results_path.relative_to(ROOT)}")


def main():
    parser = argparse.ArgumentParser(description="Score chatbot replies against the accepted answers")
    parser.add_argument("--files", nargs="*", help="responses CSV files (default: all in data/responses/)")
    args = parser.parse_args()

    if not QUESTIONS_PATH.exists():
        sys.exit(f"Missing {QUESTIONS_PATH}. Run scripts/04_combine_questions.py first.")
    questions = {q["question_id"]: q for q in read_csv(QUESTIONS_PATH)}

    files = [Path(f) for f in args.files] if args.files else sorted(RESPONSES_DIR.glob("*.csv"))
    if not files:
        sys.exit("No responses files found in data/responses/.")
    for path in files:
        score_file(path, questions)


if __name__ == "__main__":
    main()
