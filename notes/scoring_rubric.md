# Scoring Rules

These rules come from the Methods section of my Project Proposal (Section 7.3), updated after the pilot on 22 October 2026. They are applied by `scripts/06_score.py`. Finalize them BEFORE collecting the full set of chatbot replies, and do not change them afterwards.
Date finalized: [date]

## Automatic scoring

1. **Normalize** the reply and every accepted answer: lowercase, remove accents, punctuation and Markdown formatting (e.g. `**bold**`), and remove leading zeros from numbers (06 → 6).
2. **Correct (1)** if the reply contains any accepted answer (`accepted_answers` in `data/questions/questions_final.csv`) as a whole word or phrase.
   - Wikidata questions: accepted answers are the English and Malay names of the answer and their aliases.
   - MKQA questions: accepted answers are the English and Malay answers MKQA provides, after the fixes in `data/mkqa_answer_fixes.csv`.
   - Years (birth year, founding year) must match exactly.
   - **Numbers written as words** count as numbers, in English and Malay ("four", "empat", "lapan puluh dua" = 82). *(Added after the pilot: "You have to win four games" was marked wrong.)*
   - **Dates** are matched in several formats: "6 September 2018", "September 6, 2018", and the Malay month names. *(Added after the pilot: "September 6, 2018" was marked wrong.)*
   - MKQA answers with a unit (e.g. "3 minutes") also accept the number alone ("3").
3. **Incorrect (0)** otherwise.
4. **Refusals** (empty reply, "I don't know", "tidak pasti", ...) are scored as incorrect and also flagged separately.
5. **Reply language** (English / Malay / unknown) is guessed from common words and recorded for every reply. A reply with only a name or a year is "unknown".
6. Failed requests (API errors) are not scored; they are sent again.

## Manual check

A random sample of 400 replies per chatbot (50 from each of the eight language × league × condition groups) is scored by hand. Agreement between the hand scores and the automatic scores is reported with Cohen's kappa.

Pilot (66 replies, Gemini 3.1 Flash-Lite): after the two fixes above, the automatic scores agreed with a manual check of all 66 replies.

## Edge cases (suggested: confirm or change before finalizing)

- **Correct answer but in the wrong language:** scored as correct; the wrong reply language is recorded and reported separately.
- **Correct answer plus extra details** (e.g. "Marang, Terengganu, Malaysia"): scored as correct if the fact that was asked is correct.
- **A nearby but different place** (e.g. "Kuala Terengganu" when the answer is "Marang"): scored as incorrect.
- **Several possible answers including the correct one** (e.g. "either X or Y"): the automatic rule counts it as correct; the manual check measures how often this happens.
- **Spelling variations of names:** covered by the aliases and by removing accents; any other variations are caught in the manual check.
