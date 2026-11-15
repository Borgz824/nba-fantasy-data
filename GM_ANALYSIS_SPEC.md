# Fantasy GM: 20 distinct analyses, run independently for each league

League NetMon (478.l.31010, team 12): 9 categories.
League PWT (478.l.33011, team 4): 13 categories.
40 executions do NOT represent 40 distinct checks.

## Analytics contract
1. NBA player identity and full eligible universe
2. Season counting statistics
3. Rolling 7/14/30-day game logs
4. Minutes, usage, shooting attempts and efficiency
5. Injury and role/availability assessment
6. League-specific category inclusion and directions (TO lower is better)
7. Per-category contributions with sample sizes
8. Overall category-adjusted value and uncertainty
9. Current roster strengths and weaknesses
10. Complete Yahoo free-agent ownership/acquisition scan
11. Pairwise ADD/DROP delta against roster baseline
12. Eligible starting-lineup optimization for each Yahoo lineup date
13. Bench and injury-slot opportunity cost
14. Current matchup category totals and opponent analysis
15. Category win probabilities and sensitivity
16. NBA fixtures and US Eastern/Philippines date mapping
17. Short-term streaming scenarios with game counts
18. Long-term value, playoff and retention costs
19. League-wide scouting, all 16 teams and standings
20. Ranked ADD/DROP/HOLD decisions, evidence and roster-change reconciliation

## Rules
- A recommendation is NOT a transaction. No move is considered executed without user confirmation or a verified Yahoo roster/transaction change.
- Recommend any number of candidates; do not gate recommendations on remaining weekly adds.
- Yahoo position eligibility and acquisition state affect execution feasibility; distinguish statistically optimal from executable.
- Never assume unknown stats, ownership, future locks, injury return dates or roster changes.
- For FG%, FT% and 3PT%, combine makes/attempts, never average percentages unweighted.
- Distinguish short-term streamers from season-long upgrades; do not sacrifice high-value long-term players for marginal weekly gain.
- Every analysis must expose source freshness, coverage, pass/fail/unknown and category impact.
- Legacy gm_readiness.py checks are infrastructure prerequisites, NOT implementation of these 20 analytics.
- A 20/20 league analytics result may be claimed only after every analysis is actually implemented, run and validated.
