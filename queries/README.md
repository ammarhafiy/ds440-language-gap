# Wikidata Coverage Check

These queries check whether Wikidata has enough data on the Malaysia Super League (regional) and the NBA (global) to generate questions automatically from templates. They were run on the Wikidata Query Service (https://query.wikidata.org) on **13 October 2026**. Wikidata changes over time, so re-running them later may give slightly different numbers.

| File | What it checks | Results |
|---|---|---|
| `q1_clubs.rq` | Clubs per league, and how many have a home city, stadium, founding year and Malay name | `results/q1_clubs_2026-10-13.csv` |
| `q2_players.rq` | Players per league, and how many have a country, birthplace, birth date and position | `results/q2_players_2026-10-13.csv` |
| `q3_popularity.rq` | Average number of Wikimedia site links per player, and how many players have a Malay Wikipedia page | `results/q3_popularity_2026-10-13.csv` |

## Summary of results

| | Malaysia Super League | NBA |
|---|---|---|
| Clubs (with a stadium) | 18 | 37 |
| Players | 1,008 | 4,332 |
| Players with birthplace | 973 | 4,282 |
| Players with birth date | 1,003 | 4,323 |
| Average Wikimedia site links per player | 5.62 | 13.31 |
| Players with a Malay Wikipedia page | 428 (42%) | 23 (0.5%) |

## Notes

- **NBA club count in Q1 (77,381):** this number is inflated. Many items that are not teams, such as player and season items, also list the NBA as their league (P118). The real number of NBA teams is about 37 to 39, which matches the city, stadium and founding-year columns. Q3 avoids this by only counting clubs that have a home venue (P115).
- **Players** include everyone Wikidata lists as a member (P54) of a league club at any time, not only current players.
- **NBA players: 4,332 in Q2 and 4,331 in Q3.** The difference comes from Q3 only counting clubs with a home venue.
- **Site links** count links to all Wikimedia projects, mostly Wikipedia pages in different languages. Averages can be pulled up by a few very famous players, so the median should also be reported once the data is downloaded.
- The results CSVs were copied from the Query Service results tables.
