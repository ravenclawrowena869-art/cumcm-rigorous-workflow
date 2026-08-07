# Model routing and validation

Choose from the task contract and data-generating structure, not from novelty.

| Primary task | Baseline | Upgrade only when needed | Minimum validation |
|---|---|---|---|
| Explain continuous outcomes | plots, transformations, linear or generalized linear model | splines, mixed effects, GAM, nonlinear or tree model | residuals, uncertainty, grouped or out-of-sample validation |
| Repeated measurements | random-intercept model or GEE | random slopes, nonlinear mixed effects | ICC, cluster-aware split/bootstrap, residuals by subject |
| Time-series prediction | seasonal naive, moving average/EWMA, linear time features, ARIMA | boosted trees, state-space, hierarchical reconciliation, deep learning | rolling-origin backtest, group-safe features, horizon-wise errors |
| Classification | rule, logistic regression, shallow tree | calibrated boosting or ensemble | PR-AUC for imbalance, calibration, threshold costs, grouped split |
| Multi-criteria ranking | equal-weight TOPSIS or explicit rule | entropy/CRITIC/AHP combination | indicator audit, alternate weights, perturbation, Top-k stability |
| Clustering | standardized K-Means/K-Medoids or hierarchy | GMM, DBSCAN, consensus clustering | multiple K criteria, seeds/resampling, cluster profiles |
| Resource allocation | LP/MILP with complete constraints | decomposition, rolling horizon, stochastic/robust optimization | independent objective and feasibility recomputation, bounds, gap, runtime |
| Multiobjective optimization | normalized objectives, lexicographic or epsilon-constraint baseline | AUGMECON2 for discrete Pareto sets; NSGA-II only when exact methods do not scale | Pareto dominance, extreme points, normalization sensitivity, reproducibility |
| Uncertainty analysis | historical scenarios and bootstrap | Monte Carlo, stochastic programming, robust sets, CVaR | source and dependence of uncertainty, quantiles, worst case, regret |

## Selection rules

- Use the same folds, horizons, features, and metrics for model comparison.
- Separate model selection/validation from the final untouched test when enough data exist.
- Prefer rolling validation to one final split for temporal data.
- Quantify uncertainty in predicted inputs passed into optimization; do not pass only a point forecast when forecast risk affects feasibility.
- A statistically significant variable may still have negligible practical effect; report both.
- A high conditional mixed-model R2 can be driven by random effects and does not imply strong new-subject prediction.
- Do not call a change point globally optimal unless the candidate search and selection uncertainty support that claim.

## Common invalid shortcuts

- fitting imputers, scalers, PCA, or feature selection on the full dataset;
- constructing lags across region, item, subject, or device boundaries;
- choosing the winner on the final test set and reporting the same score as unbiased;
- using an optimization heuristic before defining variables and constraints;
- reporting solver success without checking balances, bounds, integrality, and business rules;
- independently sampling correlated inputs while describing the scenarios as realistic joint uncertainty;
- assigning all tied scenarios to the first alternative with `argmax`;
- presenting small numerical gains as significant without repeated or paired evidence.

## Triggered literature reminders

- Retrieve AUGMECON2 only when a MILP needs an interpretable discrete Pareto set.
- Retrieve NSGA-II only when exact MILP/epsilon-constraint methods cannot cover the required scale.
- Retrieve LightGBM after rolling validation shows a stable advantage over seasonal naive, EWMA, and statistical baselines.
- Retrieve SHAP only after a tree model is selected and explanation of its predictions is required.
