# The Language Gap: AI Chatbot Accuracy on Sports Questions in English and Malay

DS 440 Capstone, Penn State, Fall 2026
Ammar Hafiy Bin Hamdan Kamil

## Research Question

<!-- Write your research question here in your own words. -->

## Study Design

| | Global sport (NBA) | Regional sport (Malaysia Super League) |
|---|---|---|
| **English** | Group 1 | Group 2 |
| **Malay** | Group 3 | Group 4 |

Each question is asked in two conditions:
1. **No facts**: the question on its own
2. **With facts**: the question with the correct facts added to the prompt, in the same language as the question

Web search is turned off for all chatbots.

## Hypotheses

<!-- List H1-H3 here in your own words. -->

## Repository Structure

```
data/
  questions.csv        # Question set: English + Malay versions, answers, sources, date checked
  responses/           # Collected chatbot responses (one CSV per model/run)
scripts/               # Code for collecting and scoring responses
results/               # Tables and figures
notes/
  weekly_log.md        # Weekly log of time spent, progress, and blockers
  scoring_rubric.md    # Scoring rules, written before collecting responses
```

## Data Sources

- NBA Stats (official) and Basketball-Reference: NBA facts
- Malaysian Football League (official), Wikipedia season pages, Sofascore: Malaysia Super League facts
- Wikidata: official English and Malay names

A fact is only used if at least two sources agree.

## How to Run

<!-- Add instructions once scripts are written. -->

## Generative AI Disclosure

The initial folder structure, file templates, and this README template were created with Claude (Anthropic).
Research content (research question, hypotheses, question set, translations, scoring decisions, and analysis) is my own.
<!-- Update this section whenever AI is used for code or other parts of the project. -->
