# Data analyst internship: project interview guide

This guide is based on the project artifacts. No specific job description or company was supplied. Use it to practice explaining your understanding; adapt first-person statements to the work you actually did.

## What this project demonstrates

| Skill | Evidence you can open |
|---|---|
| Framing a business question | Stock-review decision in the case study |
| SQL | Seven queries using joins, CTEs, grouping, and window functions |
| Data modeling | Item-store-day facts and series/date dimensions in SQLite |
| Data quality | Validation checks, database constraints, export manifest |
| Analysis | Store/category comparisons, complete-week trends, error review |
| Communication | Business recommendation, five-minute demo, documented assumptions |
| Python | Repeatable CLI, CSV exports, tests, forecasting pipeline |
| Spreadsheet analysis | CSV tables and reproducible formulas in the analyst guide |

The repository does not demonstrate a completed Power BI/Tableau report or stakeholder work at an employer. Do not add those claims to an application.

## A 30-second project introduction

“Retail Demand Planner is a sales and inventory analysis project using 1,000 sampled M5 item-store histories. It compares seven demand forecasting methods, then uses SQL and a dashboard to inspect store and category errors and a hypothetical stock decision. The selected model reduced the subset forecast score by 23.2% against a seasonal baseline. My main analytical conclusion is that aggregate improvement hides difficult segments, so I would investigate those before using the predictions operationally.”

## Questions to prepare thoroughly

**1. What business problem does it solve?**

It supports a stock-review decision: which item-store pairs need attention, how demand may evolve, and how forecast error changes a stated one-order simulation. It does not place real orders.

**2. What is the grain of your data?**

One observed sales row is one item at one store on one date. A forecast row adds the comparison view, selected or seasonal baseline. Joining only on store or item would duplicate records.

**3. How much data did you analyze?**

The model study uses 1,000 histories spanning 1,941 days, a fixed-seed subset of M5. The SQL mart uses only their last 56 observed days: 56,000 item-days. It also includes 28 days of holdout predictions and 28 days of future forecasts. Distinguish the study scope from the mart scope.

**4. How did you check quality?**

The analysis export checks unique series IDs, 28-day date alignment, finite nonnegative values, array sizes, holdout/history agreement, and interval ordering. SQLite constraints protect primary and foreign keys. Tests reconcile SQL WAPE and inventory costs to saved evaluation results. These checks do not prove source records match real stock operations.

**5. How do you calculate WAPE?**

Sum the absolute daily forecast errors and divide by total actual demand. For actuals [0, 10] and forecasts [2, 8], WAPE is 4/10 = 40%. Per-row percentage error fails on the zero actual. Group WAPEs must be weighted by actual demand, not averaged. A zero denominator is undefined, represented by SQL NULL.

**6. What does negative bias mean?**

Total forecast demand is below actual demand. This may increase shortage exposure under a stock rule, but bias alone does not establish an actual stockout. WAPE measures magnitude; bias measures direction, so errors can cancel in bias.

**7. Why use several baseline methods?**

They make the gain credible and show the complexity tradeoff. Last-observation forecasting is weak here. The weekday blend nearly matches LightGBM on holdout, which is more informative than comparing only to a poor baseline.

**8. Why not split rows randomly?**

A real forecast cannot see later sales. Rolling-origin validation trains on earlier completed periods and predicts later ones. The last 28 days are excluded from method selection and interval calibration. Random splits could share future patterns with training.

**9. What did you find?**

The selected method improved the subset score by 23.2%, yet holdout WAPE remained 74.7%. CA_1 had the largest store WAPE at 88.7%. HOBBIES improved on its baseline but still had 107.8% WAPE. These are review signals, not explanations of cause.

**10. What action would you recommend?**

Review high-error items and store bias, get actual stock and lead-time data, and test an ordering rule under controlled assumptions. Compare the simpler weekday method before taking on the maintenance of a more complex model.

**11. What is the main SQL trap in this project?**

Sales joined to all forecast rows can duplicate actual units. Align series ID and date, filter holdout versus future, and select one forecast view. Check counts before and after joins.

**12. Why exclude partial weeks?**

A boundary week with only two observed days should not be compared with seven days of sales. The weekly query keeps full weeks and uses `LAG` within each store. The first comparison and division by zero return NULL.

**13. Why can WAPE exceed 100%?**

Absolute error can exceed observed demand, particularly for low-demand items with large forecasts. It is an error ratio, not an accuracy percentage bounded by 100%.

**14. Is 9.2% lower simulated cost the same as business savings?**

No. The calculation uses arbitrary unit costs, assumed starting stock, and one immediate order. It omits real lead times, repeated ordering, stock availability, and measured financial costs. It is evidence about a scenario, not an employer outcome.

**15. How would you use Excel?**

Import the CSVs as tables, format ratio columns as percentages, chart store WAPE and category comparisons, and calculate overall WAPE with demand weights. The exact formulas are in the analyst guide. Explain and reproduce them before listing Excel as project experience.

**16. How would you measure a real pilot?**

Agree on a baseline and decision rules in advance. Track stockouts, fill rate, excess stock, ordering costs, forecast bias, and human overrides. Choose a defensible comparison period or controlled rollout and account for promotions and assortment differences. This project has not run that pilot.

**17. What is the biggest limitation?**

Sales are not unconstrained demand: zero sales may mean no demand or unavailable stock. The 1,000-series sample, short analysis extract, pooled intervals, and simplified stock scenario limit the conclusions.

**18. Can somebody reproduce the result?**

The repo provides a lockfile, commands, data source, sample seed, model configuration, and tests. The committed case study and CSVs can be reviewed immediately. Rebuilding the dashboard and model needs the raw files. New runs record input hashes and environment versions; the older saved study has export-time metadata, not a reconstructed original training environment.

**19. What would you improve next?**

Extend analysis beyond the 56-day mart, validate more dates and series, segment sparse items, and add real inventory/lead-time data. Change one assumption at a time and evaluate on new periods. Do not tune repeatedly against the same reported holdout and keep calling it untouched.

**20. How did you verify the implementation?**

Explain a query line by line, show how its totals reconcile to the saved evaluation, and demonstrate the checks for date alignment, holdout isolation, and saved-model prediction parity. Identify one limitation that the tests cannot establish, such as whether a simulated inventory benefit would hold in a real store.

## STAR stories grounded in the project

Use these only when you can describe your own contribution. They are project stories, not invented employment history.

### Making the metric credible

- **Situation:** Sparse daily sales make row-level percentage error misleading.
- **Task:** Compare methods and store performance fairly.
- **Action:** Use time-based evaluation, multiple baselines, ratio-of-sums WAPE, and a separate scaled hierarchy score. Verify that SQL reproduces evaluation totals.
- **Result:** The saved study shows a 23.2% subset score reduction, with difficult segments still visible.
- **Short version:** “The most useful part was making the comparison defensible: time-based splits, several baselines, and SQL totals that agree with the evaluation.”

### Turning a score into a decision

- **Situation:** A single overall improvement can hide store-specific problems.
- **Task:** Produce an actionable review rather than only a model score.
- **Action:** Compare stores and categories, rank large item errors, show signed bias, and separate future quantities from historical simulated costs.
- **Result:** The analysis prioritizes CA_1 and identifies HOBBIES as difficult, with explicit next steps and limitations.
- **Short version:** “I would not recommend acting on the overall score alone. Store and category cuts show where an analyst should investigate first.”

### Keeping the demonstration reproducible

- **Situation:** A dashboard alone is hard to audit or reproduce.
- **Task:** Make the findings inspectable without a live training session.
- **Action:** Export a SQLite mart, seven SQL analyses, CSVs, a generated case study, and a checksum manifest. Keep a synthetic fallback separate from real results.
- **Result:** Reviewers can inspect the small portfolio pack immediately and rebuild the workflow with documented commands.
- **Short version:** “I separated the analysis evidence from the live service, so the case study and SQL outputs remain usable during an offline interview.”

Do not invent a team conflict, failed deployment, stakeholder approval, or company revenue to fill a behavioral answer. Use a real experience outside this project for those questions.

## Resume bullets

Adapt these to your verified contribution and understanding:

- Analyzed 1,000 sampled retail item-store sales histories; built a SQLite mart and seven SQL reports covering store/category errors, weekly trends, and inventory review.
- Compared seven forecasting methods using rolling validation; selected LightGBM achieved 23.2% lower holdout subset WRMSSE than a 28-day seasonal baseline.
- Produced an interactive dashboard, auditable CSV exports, and a business case study distinguishing simulated stock costs from measured business impact.

Suggested skills to discuss: SQL joins and window functions, SQLite, Python, KPI definition, data validation, visualization, time-series evaluation, and business communication. Add Excel only after completing the exercise. Add Power BI/Tableau only after building and understanding a report yourself.

## Questions to ask an interviewer

1. What decisions would an intern's analysis support in the first month?
2. How does the team check data quality and review SQL before using a result?
3. What makes an analysis useful to your stakeholders beyond a dashboard?

## Practice before applying

- Deliver the five-minute demonstration without reading this guide.
- Write the store WAPE query and explain its join keys from memory.
- Calculate WAPE and bias for a tiny example by hand.
- Complete the Excel exercise and explain why group percentages need weights.
- Explain one strong finding, one limitation, and one next experiment.
- Explain a design decision and the checks used to verify its behavior.

This project can support an internship application. It does not replace SQL practice, spreadsheet fluency, or understanding the business question.
