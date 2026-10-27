# Data Dictionary

All CSV files are UTF-8 (saved with a byte-order mark so Excel shows Malay text correctly). Lists inside one cell are separated by `|`. A `QID` is a Wikidata item ID (for example `Q5` = human). Empty cells mean "no value".

## Input files (written by hand)

### `templates.csv`: question and fact templates
| Column | Meaning |
|---|---|
| `template_id` | P1 birthplace, P2 birth year, C1 club home city, C2 club founding year, C3 stadium (not used) |
| `entity_type` | `player` or `club` |
| `property` | Fact asked about: `birthplace`, `birth_year`, `home_city`, `founded_year`, `stadium` |
| `use` | `yes` = template is used; `no` = left out (stadiums can change) |
| `question_en`, `question_ms` | Question template. `{desc}` = league term, `{name}` = player or club name |
| `fact_en`, `fact_ms` | Fact sentence for the "with facts" condition. `{answer}` = correct answer |
| `notes` | Which Wikidata property is used |

### `league_terms.csv`: league words used in the templates
| Column | Meaning |
|---|---|
| `league` | `msl` (Malaysia Super League) or `nba` |
| `league_name` | Full name as written on Wikidata |
| `player_desc_en`, `player_desc_ms` | e.g. "footballer" / "pemain bola sepak" |
| `club_desc_en`, `club_desc_ms` | e.g. "football club" / "kelab bola sepak" |

### `prompt_templates.csv`: prompt wording
| Column | Meaning |
|---|---|
| `language` | `en` or `ms` |
| `instruction` | First line of every prompt (asks for a short answer in the language of the question) |
| `fact_label`, `question_label` | Labels before the fact and the question ("Fact:" / "Fakta:", "Question:" / "Soalan:") |

### `mkqa_answer_fixes.csv`: MKQA answers removed before scoring
| Column | Meaning |
|---|---|
| `example_id` | MKQA question ID |
| `remove_answer` | Accepted answer that is removed (wrong, or too general such as a continent) |
| `reason` | Why it is removed |

## `raw/`: Wikidata download (script 01, 15 October 2026)

### `players_msl.csv`, `players_nba.csv`: one row per player
| Column | Meaning |
|---|---|
| `player_qid` | Wikidata ID of the player |
| `name_en`, `name_ms` | English and Malay names (Wikidata labels; Malay is empty if Wikidata has none) |
| `sitelinks` | Number of Wikimedia site links (Wikipedia pages in all languages and other Wikimedia projects); used as the popularity measure |
| `has_malay_wikipedia` | `1` if the player has a Malay Wikipedia page, else `0` |
| `birthplace_qids` | Birthplace(s) (P19), as QIDs |
| `birth_years` | Birth year(s) taken from date of birth (P569) |

### `clubs_msl.csv`, `clubs_nba.csv`: one row per club (clubs in the league, P118, with a home venue, P115)
| Column | Meaning |
|---|---|
| `club_qid` | Wikidata ID of the club |
| `name_en`, `name_ms` | English and Malay names |
| `venue_qids` | Home venue(s) (P115) |
| `hq_qids` | Headquarters location(s) (P159) |
| `admin_qids` | Located in (P131); used when there is no headquarters location |
| `founded_years` | Year(s) from inception (P571) |

### `places.csv`: names of every birthplace and city used as an answer
| Column | Meaning |
|---|---|
| `place_qid` | Wikidata ID of the place |
| `label_en`, `label_ms` | English and Malay names |
| `aliases_en`, `aliases_ms` | Other names (e.g. "KL" for Kuala Lumpur), used as accepted answers |

`download_info.txt` records the download date. The MKQA file `mkqa.jsonl.gz` also goes in `raw/` but is not stored in the repository (see `scripts/README.md`).

## `questions/`: question sets

### `questions_v1.csv`: Wikidata questions (script 02)
| Column | Meaning |
|---|---|
| `question_id` | `<league>-<QID>-<template_id>`, e.g. `msl-Q28606422-P1` |
| `league`, `entity_type`, `entity_qid` | League, `player` or `club`, and Wikidata ID |
| `entity_name_en`, `entity_name_ms` | Name used in each language (Malay falls back to English; 120 Malaysia Super League questions use a different Malay name, e.g. a different name order) |
| `template_id`, `property` | Template used and fact asked about |
| `question_en`, `question_ms` | The question in English and Malay |
| `fact_en`, `fact_ms` | The fact sentence for the "with facts" condition |
| `answer_en`, `answer_ms` | Correct answer (place name or year) in each language |
| `accepted_answers` | All accepted forms: English and Malay names plus aliases |
| `sitelinks`, `has_malay_wikipedia` | Popularity and Malay Wikipedia flag of the player (empty for clubs) |

Rules: 500 players per league sampled with seed 440 (from players with at least one usable fact), plus every club; a fact is used only if Wikidata gives exactly one value.

### `mkqa_sports_candidates.csv`: MKQA sports candidates (script 03, then reviewed)
| Column | Meaning |
|---|---|
| `example_id` | MKQA question ID |
| `question_en`, `question_ms` | Question in English and Malay (as written in MKQA) |
| `answer_type` | MKQA answer type: `entity`, `date`, `number`, `number_with_unit`, `short_phrase` |
| `answer_en`, `answer_ms` | Main answer in each language |
| `accepted_answers_en`, `accepted_answers_ms` | All accepted answers MKQA gives |
| `matched_word` | Sports keyword that matched |
| `maybe_time_sensitive` | `yes` if the wording suggests the answer can change ("last", "current", "most"...) |
| `keep` | Review decision: `yes` = used in the study, `no` = left out |
| `review_reason` | Short reason for the decision (rules: stable fact, one clear answer, correct answer key) |

### `questions_final.csv`: final question set, 2,151 questions (script 04)
| Column | Meaning |
|---|---|
| `question_id` | Wikidata IDs as above; MKQA questions are `mkqa-<example_id>` |
| `source` | `wikidata` or `mkqa` |
| `league` | `msl`, `nba`, or `mixed` (MKQA) |
| `entity_type`, `entity_qid`, `template_id`, `property` | As above (empty for MKQA) |
| `answer_type` | `place` or `year` for Wikidata; MKQA answer type for MKQA |
| `question_en`, `question_ms`, `fact_en`, `fact_ms` | Question and fact sentence (no fact sentence for MKQA) |
| `answer_en`, `answer_ms` | Main answer |
| `accepted_answers` | Cleaned list of accepted answers in both languages, used for scoring |
| `sitelinks`, `has_malay_wikipedia` | As above (Wikidata players only) |
| `source_id` | Wikidata QID or MKQA example ID |

Cleaning of `accepted_answers` (script 04): answers listed in `mkqa_answer_fixes.csv` are removed; aliases with no letters or digits (e.g. flag emojis), aliases of one or two characters (except KL, PJ, JB, NY, NJ, SF) and short everyday words (e.g. "can" for Canada) are removed, because scoring is not case-sensitive and they would match ordinary words; numbers are always kept. For MKQA date answers, the year alone is also accepted unless the year already appears in the question.

## `prompts/prompts.csv`: every prompt (script 04)
| Column | Meaning |
|---|---|
| `prompt_id` | `<question_id>-<language>-<condition>` |
| `question_id`, `source`, `league` | Links back to `questions_final.csv` |
| `language` | `en` or `ms` |
| `condition` | `no_facts` or `with_facts` (MKQA: `no_facts` only) |
| `prompt` | Exact text sent to the chatbot: instruction, then (with facts) the fact sentence, then the question, all in one language |

## `responses/`: chatbot replies (script 05)
One file per provider and model, e.g. `openai_<model>.csv`; pilot runs end in `_pilot.csv`.

| Column | Meaning |
|---|---|
| `prompt_id`, `question_id`, `source`, `league`, `language`, `condition` | Copied from `prompts.csv` |
| `provider` | `openai`, `anthropic` or `gemini` |
| `model_requested` | Model name given to the script |
| `model_returned` | Exact model version reported by the API |
| `temperature`, `max_tokens` | Settings used |
| `timestamp_utc` | When the reply was received |
| `response` | Raw reply text |
| `finish_reason` | Why the model stopped (e.g. finished, or hit the length limit) |
| `error` | Error message if the request failed or the reply was empty (these prompts are retried on the next run) |

## `scored/`: scored replies (script 06)
One file per responses file, e.g. `gemini_<model>_pilot_scored.csv`: all columns of the responses file, plus:

| Column | Meaning |
|---|---|
| `answer_en`, `answer_ms` | Main correct answer, copied from `questions_final.csv` |
| `score` | `1` = correct, `0` = incorrect, empty = request failed (not scored) |
| `matched_answer` | The accepted answer found in the reply (normalized) |
| `refusal` | `1` if the reply is empty or says it does not know (e.g. "I don't know", "tidak pasti") |
| `reply_language` | `en`, `ms`, or `unknown` (guessed from common words; a reply with only a name or a year is `unknown`) |
| `language_match` | `1` if the reply is in the language of the question, `0` if not, empty if unknown |

## `../results/`: accuracy tables (script 06)
`results/accuracy_<name>.csv`, one row per group:

| Column | Meaning |
|---|---|
| `source`, `league`, `language`, `condition` | The group |
| `n`, `correct` | Number of scored replies and number correct |
| `accuracy` | `correct / n` |
| `ci_low`, `ci_high` | 95% Wilson confidence interval for the accuracy |
| `refusals` | Number of refusals in the group |
