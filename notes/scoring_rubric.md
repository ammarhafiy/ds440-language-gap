# Scoring Rules

These rules come from the Methods section of my Project Proposal (Section 7.3), updated after the pilot on 22 October 2026. They are applied by `scripts/06_score.py`. They were finalized BEFORE any of the full-run replies were scored, and are not changed afterwards (any later change must be listed under "Changes after finalizing" below, with its date and reason, and all replies must then be scored again).

**Date finalized: 28 October 2026**

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
7. Replies to questions that are no longer in the final question set (the 9 MKQA questions removed in the re-check on 28 October 2026) are not scored.

The automatic score is the score used in the main analysis.

## Edge cases (final decisions)

| Case | Automatic score | Hand score |
|---|---|---|
| Correct answer, but in the wrong language | Correct | Correct; the wrong reply language is recorded and reported separately |
| Correct answer plus extra details (e.g. "Marang, Terengganu, Malaysia") | Correct | Correct, if the fact that was asked is correct |
| A nearby but different place (e.g. "Kuala Terengganu" when the answer is "Marang") | Incorrect | Incorrect |
| Only a broader area (e.g. "Terengganu" or "Malaysia" when the answer is "Marang") | Incorrect, unless the broader area is itself an accepted answer | Incorrect |
| Several possible answers, including the correct one (e.g. "either X or Y") | Correct (the reply contains an accepted answer) | Incorrect: the reply does not commit to one answer. How often this happens is reported |
| Spelling variation of the correct name (e.g. "Kuala Trengganu") | Correct only if the spelling is an accepted alias | Correct, if it clearly names the same place, person or team |
| Refusal or empty reply | Incorrect, flagged as refusal | Incorrect |

## Hand check (to measure how well the automatic scoring works)

- **Sample:** for each chatbot, 20 randomly chosen replies from each of the 10 groups (English / Malay × NBA / Malaysia Super League × no facts / with facts, plus English and Malay MKQA questions without facts) = **200 replies per chatbot**. Random seed 440. Failed requests are not sampled.
- **Blind:** the hand-check sheet shows the question, the accepted answers and the reply, but not the automatic score, so my hand score is not influenced by it.
- **Who:** I score every reply in the sample myself, following the edge-case rules above, without AI help.
- **Agreement:** Cohen's kappa between my hand scores and the automatic scores, plus the percentage of replies where the two agree, reported for each chatbot.
- **Disagreements:** every disagreement is listed with the reason (e.g. hedged answer, spelling variation, scoring bug).

## Review of risky replies (separate from the hand check)

These replies are read to find scoring bugs, and are **not** part of the kappa sample:

- every reply flagged as a refusal;
- every reply that gives more than one answer ("or", "either", "atau", "sama ada").

If this review finds a systematic matching problem (for example a common answer format that the script does not recognize), the rule may be fixed once, before the hand-check sample is scored. Any such fix is listed below with its date and reason, and all replies are scored again. Judgment calls (such as hedged answers) are not "fixed" in the automatic scoring; they are reported.

## Changes after finalizing

*(none so far)*

## Pilot (22 October 2026)

66 replies from Gemini 3.1 Flash-Lite: after the two fixes above (numbers written as words, dates), the automatic scores agreed with a manual check of all 66 replies. After the MKQA re-check, 64 pilot replies remain in the question set.
