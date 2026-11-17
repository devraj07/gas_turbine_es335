# Website assessment against the supplied rubric

This is a coverage and verification record, not a professor's grade or an assertion of independent peer review.

| Rubric point | Website evidence |
| --- | --- |
| Research question and motivation | `#research-question`: contemporaneous estimation, baseline comparison and scope |
| Dataset source and structure | `#source-files`: UCI attribution, publication, units, license, yearly files and source split distinction |
| Data quality and EDA | `#data-quality` through `#yearly-behaviour`: completeness, duplicates, descriptive tables, distributions, outliers, correlations, year and sequence charts |
| Preprocessing and justification | `#feature-matrix`, `#preprocessing`, `#scales`, `#redundancy`, `#distribution-shift`: exact inputs, scaling, overlap, collinearity and drift |
| Baseline and model selection | `#model-selection`: mean/linear/Ridge/tree models, reasons, alternatives and unresolved NOX selection |
| Evaluation and splits | `#evaluation-design`, `#split-sensitivity`: chronological versus random protocols, validation, formulas and comparison-year reuse |
| Model comparison and final results | `#final-results`: target/metric selectors, full score table and saved comparison CSV |
| Errors and residuals | `#residual-analysis`, `#conditional-errors`: model/target selectors, bias, tail errors and conditional errors |
| Unsupervised regimes | `#operating-regimes`: cluster selector, profiles, silhouettes, K=4 caveat and DBSCAN alternative |
| NOX investigation | `#nox-investigation`: SVR, transformations, validation and modest Log Ridge improvement |
| Multi-objective optimization | `#prediction-tradeoffs`: projections, all 56 selectable solutions, representatives, full candidate provenance and distinct forest |
| Interactive predictor | `predict/`, `#prediction-explorer`: eight inputs, actual exported fitted models, inference and validation behavior |
| Conclusions and limitations | `#limitations`: demonstrated findings, unavailable causal/operational evidence and future validation |
| References and reproducibility | `#reproducibility`, `#research-files`, `#references`: 28 numbered verified sources, all 12 notebooks, repository links, setup, configs and AI disclosure |
| Methodological reasoning | Adjacent “Why this choice?” explanations for preprocessing, shift, model choice, splitting, clusters, NOX and Pareto screening |
| Attribution | External data/research, algorithms, Python software, original project work and AI assistance explicitly separated |
| Scientific integrity | TEY energy yield; 2015 comparison; weak NOX; no causal, cluster-optimum or industrial-setpoint claims; existing research outputs preserved |
| Visual identity | White canvas, dark green typography, right navigation, responsive layout and colored scientific charts |

## Verification and limits

- Source hashes, navigation targets, full-data saved metrics, histogram totals and conditional-error populations are checked by `validate.py`.
- `check_interactions.cjs` exercises 415 control changes, all 56 Pareto selections, year/cluster/model controls, 23 SVG charts plus a correlation heatmap, and data-loading errors.
- `check_predictor.cjs` compares 50 saved Python fixtures with JavaScript inference, including tree boundary behavior.
- `check_prediction_form.cjs` checks all eight synchronized sliders, automatic graph selection, fitted-model response ranges, invalid entries, out-of-range warnings and reset behavior.
- `package_site.py` checks the deployable file allowlist and internal asset paths, including notebook downloads.
- References were checked against primary publications, the dataset repository and specific official method documentation on 15 November 2026. Rolling documentation versions may differ from pinned export packages.
- Automated DOM checks do not verify pixels, mobile keyboard behavior or screen-reader operation. Real-browser visual/accessibility inspection could not be completed because the browser automation host was unavailable. A final desktop/mobile manual review is still required before submission.
- GitHub Pages was verified live after switching to direct website/ artifact deployment. The artifact root contains the interactive index.html; the nested prediction route, model JSON and notebook downloads were checked against source files. Subsequent edits are deployed through the same checked workflow.
- The original historical environment is unknown; current export versions and this limitation are disclosed. Research notebooks were not all rerun during the website revision.

Final submission review: 17 November 2026. Input units, automatic predictor documentation, keyboard focus indicators, reduced-motion support and print styling were refined. The browser automation host remains unavailable; live HTTP and scripted interaction verification do not replace a visual desktop/mobile review.
