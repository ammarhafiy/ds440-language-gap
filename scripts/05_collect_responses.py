"""
Step 5: send the prompts to a chatbot through its API and save every reply.

Run after 04_combine_questions.py. Examples:
    # check what would be sent, without calling any API (no key needed)
    python scripts/05_collect_responses.py --provider openai --model MODEL_NAME --pilot 20 --dry-run

    # pilot: 20 questions sampled with a fixed seed (all their prompts)
    python scripts/05_collect_responses.py --provider openai --model MODEL_NAME --pilot 20

    # full run (can be stopped and restarted; finished prompts are skipped)
    python scripts/05_collect_responses.py --provider anthropic --model MODEL_NAME

Providers:
    openai     OpenAI Chat Completions API            key in OPENAI_API_KEY
               (also any OpenAI-compatible API with --base-url and --api-key-env)
    anthropic  Anthropic Messages API                 key in ANTHROPIC_API_KEY
    gemini     Google Gemini API (generateContent)    key in GEMINI_API_KEY

Use the exact model name from the provider's documentation. No tools are sent with the
requests, so the models cannot search the web.

API keys are read from environment variables, or from a file called .env in the repository
folder (one line such as OPENAI_API_KEY=...). .env is listed in .gitignore, so it is never
uploaded to GitHub. Never paste a key into a script or notebook cell that you share.

Reads:   data/prompts/prompts.csv
Writes:  data/responses/<provider>_<model>[_pilot].csv   (one row per prompt)
"""
import argparse
import csv
import os
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
PROMPTS_PATH = ROOT / "data" / "prompts" / "prompts.csv"
RESPONSES_DIR = ROOT / "data" / "responses"
SEED = 440

OUT_COLUMNS = [
    "prompt_id", "question_id", "source", "league", "language", "condition",
    "provider", "model_requested", "model_returned", "temperature", "max_tokens",
    "timestamp_utc", "response", "finish_reason", "error",
]
DEFAULT_KEY_ENV = {"openai": "OPENAI_API_KEY", "anthropic": "ANTHROPIC_API_KEY", "gemini": "GEMINI_API_KEY"}


# ---------- helpers ----------

def load_dotenv():
    """Read KEY=value lines from .env (if it exists) into the environment."""
    path = ROOT / ".env"
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def read_prompts():
    if not PROMPTS_PATH.exists():
        sys.exit(f"Missing {PROMPTS_PATH}. Run scripts/04_combine_questions.py first.")
    with open(PROMPTS_PATH, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def pilot_sample(prompts, n_questions):
    """Pick n questions with a fixed seed, spread across msl / nba / mixed, and keep all their prompts."""
    by_league = {}
    for p in prompts:
        by_league.setdefault(p["league"], set()).add(p["question_id"])
    rng = random.Random(SEED)
    leagues = sorted(by_league)
    chosen = []
    pools = {lg: sorted(by_league[lg]) for lg in leagues}
    for lg in leagues:
        rng.shuffle(pools[lg])
    while len(chosen) < n_questions and any(pools.values()):
        for lg in leagues:
            if pools[lg] and len(chosen) < n_questions:
                chosen.append(pools[lg].pop())
    chosen = set(chosen)
    return [p for p in prompts if p["question_id"] in chosen]


def done_ids(path, rewrite=False):
    """Prompt IDs that already have a reply. Rows with an error are tried again: with
    rewrite=True they are removed from the file first, so each prompt keeps one row."""
    if not path.exists():
        return set()
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    good = [r for r in rows if not r.get("error")]
    if rewrite and len(good) < len(rows):
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=OUT_COLUMNS)
            writer.writeheader()
            writer.writerows(good)
    return {r["prompt_id"] for r in good}


def safe_name(text):
    return "".join(c if c.isalnum() or c in "-." else "-" for c in text)


# ---------- API calls (each returns: text, model_returned, finish_reason) ----------

def call_openai(prompt, args, key):
    url = (args.base_url or "https://api.openai.com/v1").rstrip("/") + "/chat/completions"
    body = {"model": args.model, "messages": [{"role": "user", "content": prompt}],
            "max_completion_tokens": args.max_tokens}
    if args.temperature is not None:
        body["temperature"] = args.temperature
    r = requests.post(url, headers={"Authorization": f"Bearer {key}"}, json=body, timeout=60)
    r.raise_for_status()
    data = r.json()
    choice = data["choices"][0]
    return (choice["message"].get("content") or ""), data.get("model", ""), choice.get("finish_reason", "")


def call_anthropic(prompt, args, key):
    body = {"model": args.model, "max_tokens": args.max_tokens,
            "messages": [{"role": "user", "content": prompt}]}
    if args.temperature is not None:
        body["temperature"] = args.temperature
    headers = {"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"}
    r = requests.post("https://api.anthropic.com/v1/messages", headers=headers, json=body, timeout=60)
    r.raise_for_status()
    data = r.json()
    text = "".join(block.get("text", "") for block in data.get("content", []) if block.get("type") == "text")
    return text, data.get("model", ""), data.get("stop_reason", "")


def call_gemini(prompt, args, key):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{args.model}:generateContent"
    config = {"maxOutputTokens": args.max_tokens}
    if args.temperature is not None:
        config["temperature"] = args.temperature
    body = {"contents": [{"role": "user", "parts": [{"text": prompt}]}], "generationConfig": config}
    r = requests.post(url, headers={"x-goog-api-key": key}, json=body, timeout=60)
    r.raise_for_status()
    data = r.json()
    candidates = data.get("candidates") or [{}]
    parts = (candidates[0].get("content") or {}).get("parts", [])
    text = "".join(p.get("text", "") for p in parts)
    return text, data.get("modelVersion", ""), candidates[0].get("finishReason", "")


CALLERS = {"openai": call_openai, "anthropic": call_anthropic, "gemini": call_gemini}


def ask(prompt, args, key):
    """Call the API, retrying on rate limits and server errors."""
    for attempt in range(6):
        try:
            return CALLERS[args.provider](prompt, args, key) + ("",)
        except requests.HTTPError as e:
            status = e.response.status_code if e.response is not None else 0
            detail = e.response.text[:300] if e.response is not None else str(e)
            if status in (429, 500, 502, 503, 504) and attempt < 5:
                time.sleep(2 ** attempt * 2)
                continue
            return "", "", "", f"HTTP {status}: {detail}"
        except (requests.RequestException, KeyError, ValueError) as e:
            if attempt < 5:
                time.sleep(2 ** attempt * 2)
                continue
            return "", "", "", f"{type(e).__name__}: {e}"


# ---------- main ----------

def main():
    parser = argparse.ArgumentParser(description="Collect chatbot replies for the prompts in data/prompts/prompts.csv")
    parser.add_argument("--provider", required=True, choices=sorted(CALLERS))
    parser.add_argument("--model", required=True, help="exact model name from the provider's documentation")
    parser.add_argument("--pilot", type=int, default=0, help="only use N questions (fixed seed), e.g. 20")
    parser.add_argument("--limit", type=int, default=0, help="stop after N new prompts (for testing)")
    parser.add_argument("--temperature", default="0", help="sampling temperature, or 'none' to leave it out")
    parser.add_argument("--max-tokens", type=int, default=50, help="maximum length of each reply")
    parser.add_argument("--sleep", type=float, default=0.5, help="seconds to wait between requests")
    parser.add_argument("--base-url", default="", help="for OpenAI-compatible APIs (openai provider only)")
    parser.add_argument("--api-key-env", default="", help="name of the environment variable that holds the key")
    parser.add_argument("--out", default="", help="output CSV (default: data/responses/<provider>_<model>.csv)")
    parser.add_argument("--dry-run", action="store_true", help="show what would be sent; no API calls")
    args = parser.parse_args()
    args.temperature = None if args.temperature.lower() == "none" else float(args.temperature)

    prompts = read_prompts()
    if args.pilot:
        prompts = pilot_sample(prompts, args.pilot)

    name = f"{args.provider}_{safe_name(args.model)}" + ("_pilot" if args.pilot else "")
    out_path = Path(args.out) if args.out else RESPONSES_DIR / f"{name}.csv"
    finished = done_ids(out_path, rewrite=not args.dry_run)
    todo = [p for p in prompts if p["prompt_id"] not in finished]
    if args.limit:
        todo = todo[:args.limit]

    print(f"{len(prompts)} prompts selected, {len(prompts) - len(todo)} already done, {len(todo)} to send.")
    print(f"Output: {out_path}")

    if args.dry_run:
        for p in todo[:3]:
            print(f"\n--- {p['prompt_id']} ---\n{p['prompt']}")
        print("\nDry run only: nothing was sent and nothing was saved.")
        return

    load_dotenv()
    key_env = args.api_key_env or DEFAULT_KEY_ENV[args.provider]
    key = os.environ.get(key_env, "").strip()
    if not key:
        sys.exit(f"No API key found. Set {key_env} (see the top of this script).")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    new_file = not out_path.exists()
    errors = 0
    with open(out_path, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=OUT_COLUMNS)
        if new_file:
            writer.writeheader()
        for i, p in enumerate(todo, 1):
            text, model_returned, finish, error = ask(p["prompt"], args, key)
            errors += bool(error)
            writer.writerow({
                "prompt_id": p["prompt_id"], "question_id": p["question_id"], "source": p["source"],
                "league": p["league"], "language": p["language"], "condition": p["condition"],
                "provider": args.provider, "model_requested": args.model, "model_returned": model_returned,
                "temperature": "" if args.temperature is None else args.temperature,
                "max_tokens": args.max_tokens,
                "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "response": text.strip(), "finish_reason": finish, "error": error,
            })
            f.flush()
            if i % 50 == 0 or i == len(todo):
                print(f"  {i}/{len(todo)} done ({errors} errors)")
            if error and errors >= 10 and errors == i:
                sys.exit(f"Stopping: the first {errors} requests all failed. Last error: {error}")
            time.sleep(args.sleep)

    print(f"\nFinished. {errors} errors. Rows with errors are tried again if you run the same command.")


if __name__ == "__main__":
    main()
