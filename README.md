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

## Hypotheses

I predict that the chatbots will be more accurate in English than Malay overall, and that the biggest gap will be on the Malay questions about regional sports. I also predict that giving the chatbot the relevant facts in the prompt will raise its Malay accuracy on regional questions and narrow the gap.

<!-- Update to formal H1-H3 to match Report 2. -->

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

The initial folder structure, file templates, this README template, and the English question templates in `data/questions.csv` were created with Claude (Anthropic). The research question and hypotheses above are copied from my own Report 1.
Research content (research question, hypotheses, question set, translations, scoring decisions, and analysis) is my own.
<!-- Update this section whenever AI is used for code or other parts of the project. -->
