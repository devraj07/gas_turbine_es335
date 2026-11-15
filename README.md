# Gas turbine energy yield and emissions

A static research website and 12 notebooks studying TEY (energy yield), CO and NOX from eight operating measurements. The website explains the data audit, preprocessing, models, evaluation, operating groups and exploratory Pareto trade-offs. Its separate prediction page evaluates exported fitted models on the user's eight inputs.

## Repository

| Location | Contents |
| --- | --- |
| `data/gt_2011.csv` through `gt_2015.csv` | Original supplied yearly measurements |
| `notebook/` | All 12 original research notebooks, ordered 01-12 |
| `outputs/` | Saved comparison metrics, predictions, clustering and optimization CSVs |
| `website/` | Static HTML, CSS, JavaScript, exported models and diagnostic data |
| `website/scripts/` | Preparation, verification and deployment packaging |
| `requirements.txt` | Checked Python package versions; optional JupyterLab interface |
| `ASSESSMENT.md` | Rubric coverage and verification limits |
| `.github/workflows/pages.yml` | GitHub Pages build and deployment |

Generated figures, caches, environments, redundant notebook copies and deployment staging are ignored. Notebook figures remain embedded in the original notebooks. No dataset or saved research CSV was edited for the website.

## Dataset and attribution

Source: [UCI Gas Turbine CO and NOx Emission Data Set](https://archive.ics.uci.edu/dataset/551/gas+turbine+co+and+nox+emission+data+set), 2019, DOI [10.24432/C5WC95](https://doi.org/10.24432/C5WC95), CC BY 4.0. The local five files contain 36,733 rows and eleven numeric measurements. Obtain replacement files using the UCI download and preserve their yearly filenames.

Original publication: Heysem Kaya, Pinar Tufekci and Erdinc Uzun (2019), [Predicting CO and NOx emissions from gas turbines: novel data and a benchmark PEMS](https://journals.tubitak.gov.tr/elektrik/vol27/iss6/53/), Turkish Journal of Electrical Engineering and Computer Sciences 27(6), 4783-4796. The website provides numbered citations for the established algorithms and specific software methods. Data collection and algorithm invention are not contributions of this project.

## View the website

Python is only needed to serve or prepare files locally; visitors need JavaScript, not Python. From the repository root:

```powershell
python website/scripts/package_site.py
python -m http.server 8000 --directory .pages
```

Open `http://localhost:8000/`. The analysis page and `predict/` use relative URLs and work under a GitHub Pages project prefix. Initial prediction model download is about 24.5 MB; loading status and failures are displayed.

## Run the research

The original notebook environment was not pinned. The website export was checked with Python 3.14.4, NumPy 2.4.6, pandas 3.0.3, SciPy 1.17.1, scikit-learn 1.9.0, Matplotlib 3.10.9 and seaborn 0.13.2. These package versions are pinned in `requirements.txt`. JupyterLab is an optional, unpinned interface; it was not installed in the checked export environment. The pins do not reconstruct an unknown historical environment or guarantee identical results on every platform.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m jupyter lab
```

Open notebooks from `notebook/`, keep that directory as the notebook working directory, and run 01-12 in order. Preserve saved outputs before rerunning: notebooks write to `outputs/`. Model fitting, tuning and clustering can take time and substantial memory. The website uses saved results; it does not rerun notebooks on page load.

### Inputs and preprocessing

Exact feature order: `AT, AP, AH, AFDP, GTEP, TIT, TAT, CDP`. Targets are separately `TEY`, `CO`, `NOX`; neither year nor target values enter the final input matrix. No missing values or infinite entries occur in the supplied data. Seven repeated complete rows are retained. Statistical outlier flags do not delete rows. Native values are used with no unit conversion.

Development: 2011-2014, 29,349 rows. Comparison: 2015, 7,384 rows. Repeated inspection makes 2015 a comparison dataset, **not an untouched test set**. UCI's recommended original benchmark split differs. NOX investigations tune using 2011-2013 and validate on 2014 before refitting on 2011-2014. The separate random baseline uses all years, 80/20, seed 42; its population differs from the chronological comparison.

StandardScaler is fitted within training pipelines for Ridge, SVR and clustering. Final browser models use raw inputs. Ridge and optimization-forest searches use five expanding TimeSeriesSplit folds; row order is preserved, but omitted dates prevent asserting equal elapsed fold durations.

### Models and exact settings

| Experiment | Explicit configuration |
| --- | --- |
| TEY browser / notebook 04 | RandomForestRegressor, 100 trees, depth 15, minimum split 5, minimum leaf 2, max_features 1.0, seed 42 |
| CO browser / notebook 05 | GradientBoostingRegressor, 100 trees, learning_rate .05, depth 2, minimum split 5, minimum leaf 2, subsample .8, squared_error loss, seed 42 |
| NOX browser / notebook 03 | LinearRegression defaults, fitted intercept |
| Ridge baseline | StandardScaler + Ridge; alpha grid [.01,.1,1,10,100], five chronological folds, negative RMSE; selected TEY=100, CO=100, NOX=10 |
| SVR NOX | StandardScaler + RBF SVR; C=[1,10,100], epsilon=[.1,.5], gamma=[scale,.01]; selected 1/.1/.01; 6,000 equally spaced tuning rows and 8,000 final rows |
| NOX transforms | Natural log target / exponential inverse; Log Ridge alpha=10. PolynomialFeatures degree=2, include_bias=False, StandardScaler, Ridge alpha=10. Validation RMSE selects Log Ridge |
| K-Means | Standardized development inputs, K=2..10, selected K=4, n_init=10, seed 42, silhouette sample up to 5,000 |
| DBSCAN | Standardized inputs, eps=[.5,.7,.9,1,1.2,1.5,2], min_samples=[5,10,15,20]; retained eps=1, min_samples=10 |
| Pareto TEY forest | RandomizedSearchCV, four draws, five chronological folds, negative MAE, seed 42, refit=True; selected 150 trees, depth 30, minimum split 10, minimum leaf 2, max_features=1.0 |

Pareto forest search space: trees [150,200,300], depth [None,10,20,30], split [2,5,10], leaf [1,2,5], max_features [1.0,sqrt]. It is **different from the browser TEY forest**. CO and NOX use the documented Gradient Boosting and Linear Regression configurations. The 29,342 unique historical development input combinations produce 56 non-dominated candidates. Objectives maximize predicted TEY and minimize predicted CO/NOX. Balanced selection minimizes equal-weight Euclidean distance to the normalized ideal over the frontier; no engineering constraint or uncertainty adjustment is applied.

Unspecified parameters use library defaults. Seeds are 42 where a stochastic seed is specified. Original notebook source is authoritative; `website/assets/data/notebook-methods.json` extracts exact configuration cells and their retained text outputs. The export uses forest `n_jobs=1` instead of notebook `n_jobs=-1`. It refits the documented model configurations; it is not an original serialized checkpoint. `browser-models.json` holds actual fitted tree structures/coefficients. JavaScript uses float32 tree inputs to match scikit-learn.

### Rebuild website data and verify

After reviewing any changed research results, run these from the repository root:

```powershell
python website/scripts/prepare_data.py
python website/scripts/prepare_predictor.py
python website/scripts/prepare_analysis.py
python website/scripts/validate.py
node --check website/assets/js/app.js
node --check website/assets/js/predict.js
node website/scripts/check_interactions.cjs
node website/scripts/check_predictor.cjs
node website/scripts/check_prediction_form.cjs
python website/scripts/package_site.py
```

The preparation scripts read research CSVs and write website assets only. Hashes in provenance and analysis JSON record source bytes. All metric summaries use full comparison populations; scatter plots use disclosed deterministic subsampling. Node interaction tests use a simulated DOM, not a real browser rendering engine. Inference fixtures compare 50 Python predictions with JavaScript; form tests verify changed values, invalid input, out-of-range warnings and reset.

## Scientific limits

TEY is energy yield, not thermal efficiency. NOX accuracy is limited: the final linear model has 2015 R-squared about .158; the separate Log Ridge experiment improves this to about .196 but was not adopted in final synthesis. Correlation is not causal evidence. K=4 is not the silhouette optimum (K=2 scores higher); clusters describe historical groups, not optimal regimes. Pareto candidates are model-supported exploration, not safe industrial setpoints. None of the results establishes readiness for operational control.

## GitHub Pages

Select **Settings > Pages > Source > GitHub Actions**, then push to `main` at `https://github.com/devraj07/gas_turbine_es335` or open **Actions > Deploy research website to GitHub Pages > Run workflow > main**. The workflow copies the 12 original notebooks into the website download directory, verifies the site, and uploads only `website/`. Its `index.html` becomes the artifact root entry point; the repository README is not published as the homepage. Do not select **Deploy from a branch** with the repository root, which lets the default Jekyll build publish repository documentation. The local `.pages/` packaging utility remains available for previews. Intended URL: `https://devraj07.github.io/gas_turbine_es335/`; availability depends on a successful Pages deployment. No server backend, API key or runtime Python is required.

## AI-use disclosure

AI assistance was used to develop and revise the website, derive supplementary diagnostics, export fitted models, draft explanations and locate references. The historical notebooks' authorship process was not independently verified. The owner must review scientific claims before submission; this disclosure does not assert completed human review. Saved research metrics were not changed to improve performance. Custom website charts and interface code are project implementation; external data, established methods and Python libraries are credited separately. No external stock imagery or web fonts are used.
