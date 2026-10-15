# Scripts

Run the scripts in order from the repository folder. Each one prints a short summary when it finishes.

| Script | What it does | Output |
|---|---|---|
| `01_get_wikidata.py` | Downloads NBA and Malaysia Super League players and clubs from Wikidata, plus English and Malay names for places | `data/raw/` |
| `02_build_questions.py` | Picks 500 random players per league (fixed seed 440) and fills in the templates in `data/templates.csv` | `data/questions/questions_v1.csv` |
| `03_mkqa_sports.py` | Finds the sports questions in MKQA for manual review | `data/questions/mkqa_sports_candidates.csv` |

## Before running

1. **Malay templates:** fill in `question_ms` and `fact_ms` in `data/templates.csv`, and `player_desc_ms` and `club_desc_ms` in `data/league_terms.csv`. Keep the placeholders `{name}`, `{desc}` and `{answer}` exactly as they are. Script 02 still runs without them, but the Malay columns will be empty.
2. **MKQA:** download https://github.com/apple/ml-mkqa/raw/main/dataset/mkqa.jsonl.gz and save it as `data/raw/mkqa.jsonl.gz`. Do not unzip it.

## Option A: on your own computer

```
pip install -r requirements.txt
python scripts/01_get_wikidata.py
python scripts/02_build_questions.py
python scripts/03_mkqa_sports.py
```

## Option B: Google Colab (nothing to install)

Open a new notebook at https://colab.research.google.com and run these cells:

```
!git clone https://github.com/ammarhafiy/ds440-language-gap.git
%cd ds440-language-gap
!pip install -r requirements.txt
!python scripts/01_get_wikidata.py
!python scripts/02_build_questions.py
```

For MKQA in Colab:

```
!wget -O data/raw/mkqa.jsonl.gz https://github.com/apple/ml-mkqa/raw/main/dataset/mkqa.jsonl.gz
!python scripts/03_mkqa_sports.py
```

Colab files disappear when the session ends. Download the new files from `data/raw/` and `data/questions/` (folder icon on the left), then upload them to GitHub.

## After running

- Open `data/questions/mkqa_sports_candidates.csv` and fill in the `keep` column (yes / no) for every row.
- Check about 20 rows of `data/questions/questions_v1.csv` by hand against Wikipedia to make sure the answers look right.
