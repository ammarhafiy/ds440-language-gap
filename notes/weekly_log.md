# Weekly Log

Shared with Leona at each weekly meeting.

## Week 1: 5 to 8 October 2026

| Day | Date | Hours | What I did | Evidence |
|---|---|---|---|---|
| Mon | Oct 5 | 30 mins | Zoom meeting with Prof. Thomson on my make-up plan | Make-up plan document |
| Tue | Oct 6 | 1 hour 30 mins | Chose my project topic and found related papers | Report 1 references |
| Wed | Oct 7 | 5 hours | Wrote and submitted Report 1 (Topic) | Report 1 submission |
| Thu | Oct 8 | 15 mins | Set up GitHub repo: folders, README, data templates | This repository |
| Thu | Oct 8 | 1 hour | Prepared 20 pilot questions; translated all into Malay | `data/pilot/questions.csv` |
| Thu | Oct 8 | 30 mins | Studied statistical methods for Report 3 | |
| Thu | Oct 8 | 15 mins | Set up kanban board, scheduled Zoom meeting with Leona | GitHub Projects board |

**Total hours:** 9 hours

---

## Week 2: 8 to 15 October 2026

| Day | Date | Hours | What I did | Evidence |
|---|---|---|---|---|
| Thu | Oct 8 | [1 hour] | Prepared briefing slides for my first weekly meeting | Week 1 briefing slides |
| Thu | Oct 8 | [10 mins] | Weekly meeting with Leona (Zoom). Feedback: use existing datasets with thousands of data points instead of hand-written questions | Meeting notes |
| Mon | Oct 12 | [30 mins] | Reviewed existing English and Malay question datasets (MKQA, Global-MMLU, MalayMMLU, Belebele) | |
| Mon | Oct 12 | [15 mins] | Compared two redesign options: MKQA + Wikidata, or Global-MMLU | |
| Tue | Oct 13 | [15 mins] | Ran Wikidata queries to check coverage of Malaysia Super League and NBA players and clubs | `queries/` |
| Tue | Oct 13 | [30 mins] | Updated GitHub repo: added queries and results, moved pilot questions, updated this log | Repository commits |
| Tue | Oct 13 | [10 mins] | Updated the kanban board for the new data plan | GitHub Projects board |
| Tue–Thu | Oct 13–15 | [5 hours] | Wrote Report 2 – Introduction (Sections 1–4) and checked the references | Report 2 |
| Thu | Oct 15 | [15 mins] | Translated the question templates into Malay | `data/templates.csv` |
| Thu | Oct 15 | [30 mins] | Ran the data scripts in Google Colab: downloaded Wikidata data, built the question set, found MKQA sports questions | `data/raw/`, `data/questions/` |
| Thu | Oct 15 | [30 mins] | Uploaded the scripts, templates and results to GitHub | Repository commits |

**Total hours:** [__]

**Progress this week:**
- Redesigned the data plan after Leona's feedback.
- Confirmed that Wikidata has enough Malaysia Super League data: 18 clubs and about 1,000 players with birthplace and birth date.
- Found that NBA players have more Wikimedia site links on average (13.3 vs 5.6), but far more Malaysia Super League players have a Malay Wikipedia page (42% vs 0.5%).
- Wrote Report 2 – Introduction.
- Built the question set: 2,063 questions in English and Malay (500 random players per league, plus all clubs).
- Found 681 possible sports questions in MKQA to review.

**Blockers:**
- Getting feedback on the new data plan (presenting it at this week's meeting).
- Not sure where to submit my individual reports.
- Need to choose the chatbots and check API access and cost.

**Plan for next week:**
- Write and submit Report 3 – Methods (due Oct 20, 1:30 PM).
- Spot-check 20 generated questions against Wikipedia.
- Review the 681 MKQA sports questions and fill in the "keep" column.
- Choose 2–3 chatbots and set up API access.
- Write the script that collects chatbot answers and test it on the pilot questions.
- Prepare the methods briefing (Oct 22/24).
