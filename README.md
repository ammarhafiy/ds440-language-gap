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
2. **With facts**: the question with the correct facts added to the prompt, in the same language as the question

Web search is turned off for all chatbots.

**Data plan (updated October 2026):** after feedback on 8 October 2026, the study uses existing data at a scale of thousands of data points instead of hand-written questions:

- **Global questions:** sports questions from MKQA, which has the same questions in English and Malay with answers already provided.
- **Regional and global player/club questions:** generated automatically from Wikidata with the same templates for NBA and Malaysia Super League players and clubs, in English and Malay. Only facts that do not change over time are used (for example birthplace, birth year, a club's home city, stadium and founding year).
- **Scoring:** chatbot answers are checked automatically against the correct answers and their aliases, and a sample is checked by hand.

## Hypotheses

I predict that the chatbots will be more accurate in English than Malay overall, and that the biggest gap will be on the Malay questions about regional sports. I also predict that giving the chatbot the relevant facts in the prompt will raise its Malay accuracy on regional questions and narrow the gap.

<!-- Update to formal hypotheses to match Report 2. -->

## Data Coverage Check (Wikidata, 13 October 2026)

| | Malaysia Super League | NBA |
|---|---|---|
| Clubs (with a stadium) | 18 | 37 |
| Players | 1,008 | 4,332 |
| Players with birthplace | 973 | 4,282 |
| Players with birth date | 1,003 | 4,323 |
| Average Wikimedia site links per player | 5.62 | 13.31 |
| Players with a Malay Wikipedia page | 428 (42%) | 23 (0.5%) |

Queries and full results are in `queries/`.

## Repository Structure

```
data/
  pilot/               # 20 hand-written pilot questions (English + Malay), used to test scripts
  responses/           # Collected chatbot responses (one CSV per model/run)
queries/               # Wikidata SPARQL queries and their results
scripts/               # Code for building questions, collecting and scoring responses
results/               # Tables and figures
notes/
  weekly_log.md        # Weekly log of time spent, progress, and blockers
  scoring_rubric.md    # Scoring rules
```

## Data Sources

- **MKQA** (Longpre et al., 2021): 10,000 questions with answers, human-translated into 26 languages including Malay. License: CC BY-SA 3.0.
- **Wikidata** (https://www.wikidata.org): facts about NBA and Malaysia Super League players and clubs, plus English and Malay names. License: CC0.

## How to Run

<!-- Add instructions once scripts are written. -->

## Generative AI Disclosure

The initial folder structure, file templates, this README template, and the English question templates in `data/pilot/questions.csv` were created with Claude (Anthropic). The Wikidata queries in `queries/` were written with Claude; I ran them myself on the Wikidata Query Service and checked the results. The October 2026 update to this README was also prepared with Claude. The research question and hypotheses above are copied from my own Report 1.
Research content (research question, hypotheses, translations, scoring decisions, and analysis) is my own.
<!-- Update this section whenever AI is used for code or other parts of the project. -->
