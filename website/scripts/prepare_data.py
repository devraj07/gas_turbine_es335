"""Build public assets using existing results only. Run from any directory."""
import csv
import hashlib
import json
import math
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'website/assets/data'
OUT.mkdir(parents=True, exist_ok=True)
sources = {}

def read(path):
    p = ROOT / path
    sources[path] = hashlib.sha256(p.read_bytes()).hexdigest()
    with p.open(encoding='utf-8-sig', newline='') as f:
        rows = list(csv.DictReader(f))
    for row in rows:
        for k, v in row.items():
            try:
                row[k] = float(v) if v else None
            except (ValueError, TypeError):
                pass
    return rows

def result(path):
    return read('outputs/' + path + '.csv')

features = ['AT', 'AP', 'AH', 'AFDP', 'GTEP', 'TIT', 'TAT', 'CDP']
targets = ['TEY', 'CO', 'NOX']
measurements = features + targets
years = {str(y): read(f'data/gt_{y}.csv') for y in range(2011, 2016)}
all_rows = [r for rows in years.values() for r in rows]
histograms = {}
for col in measurements:
    vals = [r[col] for r in all_rows]
    low, high = min(vals), max(vals)
    bins = [0] * 30
    for value in vals:
        bins[min(29, int((value-low)/(high-low)*30))] += 1
    histograms[col] = [{'x': low+(i+.5)*(high-low)/30, 'y': n} for i,n in enumerate(bins)]
data = {
    'features': features, 'targets': targets,
    'counts': {y: len(rows) for y,rows in years.items()},
    'missing': sum(v is None for r in all_rows for v in r.values()),
    'infinite': sum(isinstance(v, float) and not math.isfinite(v) for r in all_rows for v in r.values()),
    'duplicates': sum(len(rows)-len({tuple(r.items()) for r in rows}) for rows in years.values()),
    'histograms': histograms,
    'yearMeans': {col: [{'x': int(y), 'y': sum(r[col] for r in rows)/len(rows)} for y,rows in years.items()] for col in measurements},
    'observations': [dict(r, Year=int(y)) for y,rows in years.items() for r in rows[::40]],
    'models': result('all_models_comparison'),
    'selected': result('final_project_synthesis/final_selected_model_performance'),
    'correlations': result('eda_correlation_matrix'),
    'shift': result('final_project_synthesis/nox_feature_shift_summary'),
    'silhouette': result('unsupervised/kmeans_silhouette_results'),
    'clustering': result('unsupervised/clustering_comparison'),
    'regimeYears': result('unsupervised/year_wise_cluster_distribution'),
    'representatives': result('multi_objective_optimization/pareto_representative_solutions'),
    'pareto': result('multi_objective_optimization/pareto_optimal_operating_points'),
    'svr': result('nox_svr/nox_model_comparison_2015'),
    'transforms': result('nox_target_transform/nox_validation_model_comparison_2014'),
    'logRidge': result('nox_target_transform/nox_selected_model_2015_metrics'),
    'errorDirection': result('nox_residual_feature_shift/over_under_prediction_summary'),
    'limitations': result('final_project_synthesis/project_limitations'),
}
candidates = result('multi_objective_optimization/optimization_candidate_predictions')
data['candidateCount'] = len(candidates)
data['candidates'] = candidates[::12]
data['predictions'] = {}
for target, file, key in [('TEY','random_forest_2015_predictions','TEY_random_forest'), ('CO','gradient_boosting_2015_predictions','CO_gradient_boosting'), ('NOX','baseline_2015_predictions','NOX_linear_regression_pred')]:
    data['predictions'][target] = [{'x':r[target+'_actual'], 'y':r[key]} for r in result(file)[::10]]
data['residuals'] = [{'x':r['Predicted_NOX'], 'y':r['Residual']} for r in result('nox_residual_feature_shift/linear_regression_2015_residuals')[::10]]
def profiles(name, cols):
    path = ROOT / ('outputs/unsupervised/' + name + '.csv')
    sources[str(path.relative_to(ROOT)).replace('\\','/')] = hashlib.sha256(path.read_bytes()).hexdigest()
    rows = list(csv.reader(path.open(encoding='utf-8-sig')))
    return [dict(Cluster=int(r[0]), Count=int(r[1]), **{c:float(r[2+6*i]) for i,c in enumerate(cols)}) for r in rows[3:]]
data['clusters'] = profiles('kmeans_cluster_profiles', targets)
data['clusterFeatures'] = profiles('kmeans_feature_profiles', features)
data['notebooks'] = [p.name for p in sorted((ROOT/'notebook').glob('*.ipynb'))]
for name in ['all_models_comparison.csv','final_project_synthesis/final_selected_model_performance.csv','multi_objective_optimization/pareto_representative_solutions.csv','multi_objective_optimization/pareto_optimal_operating_points.csv']:
    shutil.copyfile(ROOT/'outputs'/name, OUT/Path(name).name)
nbdir = ROOT/'website/assets/notebooks'
nbdir.mkdir(exist_ok=True)
for p in sorted((ROOT/'notebook').glob('*.ipynb')):
    shutil.copyfile(p, nbdir/p.name)
(OUT/'research.json').write_text(json.dumps(data,ensure_ascii=False,allow_nan=False,separators=(',',':')),encoding='utf-8')
(OUT/'provenance.json').write_text(json.dumps({'sources_sha256':sources,'sampling':{'observations':'Every 40th row per year','predictions':'Every 10th row','candidates':'Every 12th row, plus all Pareto points separately'},'aggregations':'30 equal-width histogram bins; arithmetic yearly means; no model fitting'},indent=2),encoding='utf-8')
print(f'Prepared {len(all_rows):,} observations; {len(candidates):,} candidates; {len(data["pareto"])} Pareto points.')
