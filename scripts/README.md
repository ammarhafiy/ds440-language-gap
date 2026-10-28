# Scripts

Run the scripts in order from the repository folder. Each one prints a short summary when it finishes. Every output column is described in `data/README.md`.

| Script | What it does | Output |
|---|---|---|
| `01_get_wikidata.py` | Downloads NBA and Malaysia Super League players and clubs from Wikidata, plus English and Malay names and aliases for places | `data/raw/` |
| `02_build_questions.py` | Picks 500 random players per league (fixed seed 440) and fills in the templates in `data/templates.csv` | `data/questions/questions_v1.csv` |
| `03_mkqa_sports.py` | Finds the sports questions in MKQA for manual review | `data/questions/mkqa_sports_candidates.csv` |
| `04_combine_questions.py` | Combines the Wikidata questions and the kept MKQA questions (`final_keep` = yes after the re-check), cleans the accepted answers, and writes every prompt | `data/questions/questions_final.csv`, `data/prompts/prompts.csv` |
| `05_collect_responses.py` | Sends the prompts to a chatbot API and saves every reply | `data/responses/<provider>_<model>.csv` |
| `06_score.py` | Scores every reply against the accepted answers and makes an accuracy table per group (95% Wilson confidence intervals) | `data/scored/<name>_scored.csv`, `results/accuracy_<name>.csv` |

## Before running

1. **Malay templates:** `question_ms` and `fact_ms` in `data/templates.csv`, `player_desc_ms` and `club_desc_ms` in `data/league_terms.csv`, and the Malay `instruction` in `data/prompt_templates.csv` must be filled in. Keep the placeholders `{name}`, `{desc}` and `{answer}` exactly as they are.
2. **MKQA:** download https://github.com/apple/ml-mkqa/raw/main/dataset/mkqa.jsonl.gz and save it as `data/raw/mkqa.jsonl.gz`. Do not unzip it.
3. **Reproducing the study exactly:** skip script 01 and use the saved Wikidata download in `data/raw/` (15 October 2026). Running 01 again downloads today's Wikidata, which may have changed.

## Option A: on your own computer

```
pip install -r requirements.txt
python scripts/01_get_wikidata.py
python scripts/02_build_questions.py
python scripts/03_mkqa_sports.py
# review the keep column in data/questions/mkqa_sports_candidates.csv
python scripts/04_combine_questions.py
python scripts/05_collect_responses.py --provider openai --model MODEL_NAME --pilot 20 --dry-run
```

## Option B: Google Colab (nothing to install)

Open a new notebook at https://colab.research.google.com and run these cells:

```
!git clone https://github.com/ammarhafiy/ds440-language-gap.git
%cd ds440-language-gap
!pip install -r requirements.txt
!python scripts/04_combine_questions.py
```

Colab files disappear when the session ends. Download new files (folder icon on the left) and upload them to GitHub.

## Collecting chatbot replies (script 05)

**API key.** Each provider needs its own key from its developer website.
- **Colab:** click the key icon (Secrets) on the left, add a secret named e.g. `OPENAI_API_KEY`, allow notebook access, then run:
  ```
  from google.colab import userdata
  import os
  os.environ["OPENAI_API_KEY"] = userdata.get("OPENAI_API_KEY")
  ```
- **Own computer:** create a file called `.env` in the repository folder with one line, e.g. `OPENAI_API_KEY=...`. It is listed in `.gitignore`, so it is never uploaded.

Never paste a key directly into a script or a shared notebook.

**Commands.** Use the exact model name from the provider's documentation.

```
# 1. Check the prompts without calling the API (no key needed)
python scripts/05_collect_responses.py --provider openai --model MODEL_NAME --pilot 20 --dry-run

# 2. Pilot: 20 questions sampled with seed 440 (66 prompts), saved as data/responses/<provider>_<model>_pilot.csv
python scripts/05_collect_responses.py --provider openai --model MODEL_NAME --pilot 20

# 3. Full run (8,410 prompts). It can be stopped and restarted: finished prompts are skipped
python scripts/05_collect_responses.py --provider openai --model MODEL_NAME
```

| Provider | `--provider` | Key variable |
|---|---|---|
| OpenAI | `openai` | `OPENAI_API_KEY` |
| Anthropic | `anthropic` | `ANTHROPIC_API_KEY` |
| Google Gemini | `gemini` | `GEMINI_API_KEY` |
| Any OpenAI-compatible API (e.g. SEA-LION; check its documentation for the address) | `openai` with `--base-url URL --api-key-env NAME` | the name you choose |

Defaults: temperature 0 and a maximum reply length of 50 tokens. Check the pilot file: if replies are empty or cut off (`finish_reason` shows the length limit), raise `--max-tokens`. Some newer models count hidden "thinking" toward this limit, and some do not accept a temperature setting; use `--temperature none` for those. An empty reply is recorded as an error, so it is sent again the next time you run the same command.

`--extra-body` adds extra settings to every request (OpenAI-compatible APIs only). SEA-LION example, with the model's "thinking" turned off so it answers directly:

```
python scripts/05_collect_responses.py --provider openai --base-url https://api.sea-lion.ai/v1 \
  --api-key-env SEALION_API_KEY --model MODEL_NAME --sleep 6 \
  --extra-body '{"chat_template_kwargs": {"enable_thinking": false}}'
```

SEA-LION's free API allows 10 requests per minute, so use `--sleep 6`.

## Scoring replies (script 06)

```
# score every file in data/responses/
python scripts/06_score.py

# or only one file
python scripts/06_score.py --files data/responses/gemini_gemini-3.1-flash-lite_pilot.csv
```

It prints the accuracy table and saves the scored replies in `data/scored/` and the table in `results/`. The rules are in `notes/scoring_rubric.md`. No API key is needed.

## After running

- Check that `data/responses/..._pilot.csv` has a reply in every row and that the `error` column is empty.
- Look through `data/scored/..._scored.csv`: for each reply marked 0, check that it really is wrong.
- Spot-check questions against Wikipedia (a random sample of 20 Wikidata questions and the kept MKQA questions). Done on 28 October 2026: see Quality Checks in the main README.
