# Scoring Rules

These rules come from the Methods section of my Project Proposal (Section 7.3). Finalize them BEFORE collecting the full set of chatbot replies, and do not change them afterwards.
Date finalized: [date]

## Automatic scoring

1. **Normalize** the reply and every accepted answer: lowercase, remove punctuation and accents.
2. **Correct (1)** if the reply contains any accepted answer (`accepted_answers` in `data/questions/questions_final.csv`) as a whole word or phrase.
   - Wikidata questions: accepted answers are the English and Malay names of the answer and their aliases.
   - MKQA questions: accepted answers are the English and Malay answers MKQA provides, after the fixes in `data/mkqa_answer_fixes.csv`.
   - Years (birth year, founding year) must match exactly. MKQA numbers and dates are matched in the forms MKQA lists.
3. **Incorrect (0)** otherwise.
4. **Refusals** ("I don't know", no answer, empty reply) are scored as incorrect and also flagged separately.
5. **Reply language** is detected automatically and recorded for every reply.

## Manual check

A random sample of 400 replies per chatbot (50 from each of the eight language × league × condition groups) is scored by hand. Agreement between the hand scores and the automatic scores is reported with Cohen's kappa.

## Edge cases (suggested: confirm or change before finalizing)

- **Correct answer but in the wrong language:** scored as correct; the wrong reply language is recorded and reported separately.
- **Correct answer plus wrong extra details:** scored as correct if the fact that was asked is correct.
- **Several possible answers including the correct one** (e.g. "either X or Y"): the automatic rule counts it as correct; the manual check measures how often this happens.
- **Spelling variations of names:** covered by the aliases and by removing accents; any other variations are caught in the manual check.
