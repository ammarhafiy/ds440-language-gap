# The Language Gap: AI Chatbot Accuracy on Sports Questions in English and Malay

DS 440 Capstone, Penn State, Fall 2026
Ammar Hafiy Bin Hamdan Kamil

## Research Question

When AI chatbots answer sports questions less accurately in Malay, is that because of the language, a lack of knowledge about local sports, or a mix of both?

## Study Design

| | Global sport (NBA) | Regional sport (Malaysia Super League) |
|---|---|---|
| **English** | Group 1 | Group 2 |
| **Malay** | Group 3 | Group 4 |

Each question is asked in two conditions:
1. **No facts**: the question on its own
2. **With facts**: the same question with the correct fact added to the prompt, in the same language as the question

The chatbots are queried through their APIs with no tools enabled, so they cannot search the web.

**Data plan (updated October 2026):** after feedback on 8 October 2026, the study uses existing data at a scale of thousands of questions instead of hand-written questions:

- **Player and club questions (NBA = global, Malaysia Super League = regional):** generated from Wikidata with the same four templates for both leagues, in English and Malay. Only facts that do not change over time and have exactly one value in Wikidata are used: a player's birthplace and birth year, and a club's home city and founding year.
- **Real user questions:** sports questions from MKQA, which has the same questions in English and Malay (human translations) with answers. These cover mixed, mostly American and international sports, so they are used for Hypothesis 1 (English vs Malay) only.
- **Scoring:** replies are checked automatically against the accepted answers and their aliases, and a random sample is checked by hand.

## Hypotheses

- **H1:** Without facts, chatbots answer English questions more accurately than the same questions in Malay.
- **H2:** The English–Malay accuracy gap is wider for Malaysia Super League questions than for NBA questions.
- **H3:** Adding the correct facts to the prompt (in the language of the question) shrinks the English–Malay gap for Malaysia Super League questions.
- **H4:** For Malay questions, players who have a Malay Wikipedia page are answered more accurately than players who do not, even after taking overall popularity (number of Wikimedia site links) into account.

Full wording and references are in Report 2 (Introduction).

## Question Set (Wikidata download of 15 October 2026)

| Source | Malaysia Super League | NBA | Mixed sports | Total |
|---|---|---|---|---|
| Wikidata: players (birthplace, birth year) | 977 | 984 | – | 1,961 |
| Wikidata: clubs (home city, founding year) | 31 | 71 | – | 102 |
| MKQA (88 kept of 681 sports candidates) | – | – | 88 | 88 |
| **Total** | **1,008** | **1,055** | **88** | **2,151** |

Every question has an English and a Malay version. Prompts per chatbot: Wikidata questions × 2 languages × 2 conditions (8,252) + MKQA questions × 2 languages × no facts only (176) = **8,428**.

## Data Coverage Check (Wikidata, 13 October 2026)

| | Malaysia Super League | NBA |
|---|---|---|
| Clubs (with a stadium) | 18 | 37 |
| Players | 1,008 | 4,332 |
| Players with birthplace | 973 | 4,282 |
| Players with birth date | 1,003 | 4,323 |
| Average Wikimedia site links per player | 5.62 | 13.31 |
| Players with a Malay Wikipedia page | 428 (42%) | 23 (0.5%) |

Queries and full results are in `queries/`. The 15 October download used for the question set has 4,331 NBA players; the other numbers are the same.

## Pipeline

| Step | Script | Output |
|---|---|---|
| 1. Ingest Wikidata | `scripts/01_get_wikidata.py` | `data/raw/` (players, clubs, place names) |
| 2. Build Wikidata questions | `scripts/02_build_questions.py` | `data/questions/questions_v1.csv` |
| 3. Find MKQA sports questions | `scripts/03_mkqa_sports.py` | `data/questions/mkqa_sports_candidates.csv` (then reviewed: `keep` column) |
| 4. Combine questions and write prompts | `scripts/04_combine_questions.py` | `data/questions/questions_final.csv`, `data/prompts/prompts.csv` |
| 5. Collect chatbot replies | `scripts/05_collect_responses.py` | `data/responses/<provider>_<model>.csv` |

Scoring and analysis scripts will be added next. Every column of every data file is described in [`data/README.md`](data/README.md).

## How to Run

Requires Python 3.9 or newer. See `scripts/README.md` for details, including Google Colab and API keys.

```
pip install -r requirements.txt
python scripts/01_get_wikidata.py       # download players, clubs and place names from Wikidata
python scripts/02_build_questions.py    # build the Wikidata questions (fixed seed 440)
python scripts/03_mkqa_sports.py        # find MKQA sports questions (needs data/raw/mkqa.jsonl.gz)
python scripts/04_combine_questions.py  # final question set + all prompts
python scripts/05_collect_responses.py --provider openai --model MODEL_NAME --pilot 20
```

Step 1 queries the live Wikidata service, so running it again later can give slightly different data. To reproduce this study exactly, skip step 1 and use the saved download in `data/raw/` (15 October 2026).

## Repository Structure

```
data/
  README.md               # Data dictionary: every file and column
  templates.csv           # Question and fact templates (English + Malay)
  league_terms.csv        # Words used for each league (e.g. "footballer"), English + Malay
  prompt_templates.csv    # Prompt instruction and labels (English + Malay)
  mkqa_answer_fixes.csv   # Wrong or too-general MKQA answers removed before scoring
  raw/                    # Wikidata download (15 Oct 2026); MKQA file is downloaded separately
  questions/              # Question sets made by scripts 02-04
  prompts/                # Every prompt sent to the chatbots (script 04)
  responses/              # Chatbot replies, one CSV per provider/model (script 05)
  pilot/                  # 20 hand-written pilot questions from week 1 (no longer used)
queries/                  # Wikidata SPARQL queries used for the coverage check
scripts/                  # Pipeline scripts 01-05
notes/
  weekly_log.md           # Weekly log of time spent, progress, and blockers
```

## Data Sources and Licences

- **Wikidata** (https://www.wikidata.org): facts about NBA and Malaysia Super League players and clubs, with English and Malay names. Licence: CC0 (public domain).
- **MKQA** (S. Longpre, Y. Lu and J. Daiber, "MKQA: A linguistically diverse benchmark for multilingual open domain question answering," TACL, 2021; https://github.com/apple/ml-mkqa): 10,000 questions with answers in 26 languages including Malay. Licence: CC BY-SA 3.0. The MKQA questions and answers included in `data/questions/` (in `mkqa_sports_candidates.csv` and `questions_final.csv`) are shared under the same licence, with this attribution. The full MKQA file is not stored here; download it with the link in `scripts/README.md`.

## Data Handling and Ethics

- **Public data only:** all source data are public and openly licensed. The questions only use public facts (birthplace, birth year) about professional athletes and public facts about clubs. No private or personal data are collected.
- **Chatbot replies** are collected through the providers' official APIs, following their terms of use, and are stored only in this repository for research.
- **API keys** are never written into code or uploaded: they are read from environment variables or a local `.env` file, which is listed in `.gitignore`.
- **Fixed inputs:** the Wikidata download date (15 October 2026), the random seed (440), the prompts, and the model name, version, settings and date of every reply are all recorded, so results can be checked and repeated.
- **AI use and possible bias:** an AI assistant (Claude, a model trained mainly on English text) helped write the code and did a first-pass review of the MKQA questions. To limit bias, every question comes from fixed templates or from MKQA's human-written questions, the Malay templates were translated by me, and I re-check the MKQA review. Details are in the disclosure below.

## Generative AI Disclosure

The initial folder structure, file templates, this README, the data dictionary (`data/README.md`), and the English question templates in `data/pilot/questions.csv` were created with Claude (Anthropic). The Wikidata queries in `queries/` were written with Claude; I ran them myself on the Wikidata Query Service and checked the results. The scripts in `scripts/` (01–05) and `requirements.txt` were written with Claude; I ran the scripts myself and checked their output. Claude drafted the English question templates (`data/templates.csv`, `data/league_terms.csv`) and the English prompt instruction (`data/prompt_templates.csv`), which I reviewed. The Malay templates, Malay league terms and Malay prompt instruction are my own translations. Claude did the first-pass review of the 681 MKQA sports candidates (`keep` and `review_reason` columns) using written rules (stable fact, one clear answer, correct answer key), and proposed the answer fixes in `data/mkqa_answer_fixes.csv`; I am re-checking all kept questions and a random sample of the rejected ones. The research question and hypotheses are my own (Reports 1 and 2).
<!-- Update this section whenever AI is used for code or other parts of the project. -->
