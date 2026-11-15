"""Read-only analysis of source data and saved predictions for the research page."""
from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd
from scipy.stats import ks_2samp
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'website/assets/data'
FEATURES = ['AT', 'AP', 'AH', 'AFDP', 'GTEP', 'TIT', 'TAT', 'CDP']
TARGETS = ['TEY', 'CO', 'NOX']
COLS = FEATURES + TARGETS
sources = {}

def read(path):
    p = ROOT / path
    sources[path] = hashlib.sha256(p.read_bytes()).hexdigest()
    return pd.read_csv(p)

def records(frame):
    return json.loads(frame.to_json(orient='records', double_precision=12))

years = {str(y): read(f'data/gt_{y}.csv') for y in range(2011, 2016)}
all_data = pd.concat([df.assign(Year=int(year)) for year, df in years.items()], ignore_index=True)
dev = all_data[all_data.Year < 2015]
comp = all_data[all_data.Year == 2015]
periods = {'all': all_data, 'development': dev, **years}
result = dict(features=FEATURES, targets=TARGETS, periods={}, files=[], correlations={}, errors={}, hashes=sources)

def histogram(values, edges):
    counts, _ = np.histogram(values, bins=edges)
    return [{'x': float((edges[i]+edges[i+1])/2), 'y': int(n), 'percent': float(100*n/len(values)), 'low':float(edges[i]), 'high':float(edges[i+1])} for i,n in enumerate(counts)]

edges = {col: np.linspace(all_data[col].min(), all_data[col].max(), 33) for col in COLS}
for name, frame in periods.items():
    stats = []
    for col in COLS:
        s = frame[col]
        q = s.quantile([.01,.05,.25,.5,.75,.95,.99])
        low, high = q[.25]-1.5*(q[.75]-q[.25]), q[.75]+1.5*(q[.75]-q[.25])
        stats.append(dict(variable=col, role='Input' if col in FEATURES else 'Target', valid=int(s.count()), missing=int(s.isna().sum()), missingPercent=float(s.isna().mean()*100), zeros=int(s.eq(0).sum()), unique=int(s.nunique()), mean=float(s.mean()), std=float(s.std()), min=float(s.min()), p01=float(q[.01]), p05=float(q[.05]), q1=float(q[.25]), median=float(q[.5]), q3=float(q[.75]), p95=float(q[.95]), p99=float(q[.99]), max=float(s.max()), skew=float(s.skew()), iqr=float(q[.75]-q[.25]), outliers=int(((s<low)|(s>high)).sum()), outlierPercent=float(((s<low)|(s>high)).mean()*100)))
    result['periods'][name] = dict(rows=len(frame), columns=11, missing=int(frame[COLS].isna().sum().sum()), infinite=int(np.isinf(frame[COLS]).sum().sum()), duplicateMeasurements=int(frame.duplicated(COLS).sum()), duplicateInputs=int(frame.duplicated(FEATURES).sum()), statistics=stats, histograms={col:histogram(frame[col].to_numpy(), edges[col]) for col in COLS})

for year, frame in years.items():
    p=ROOT/f'data/gt_{year}.csv'
    result['files'].append(dict(file=p.name,year=int(year),rows=len(frame),columns=len(frame.columns),missing=int(frame.isna().sum().sum()),duplicates=int(frame.duplicated().sum()),sizeKB=round(p.stat().st_size/1024,1),schemaMatches=set(frame.columns)==set(COLS),numericColumns=int(len(frame.select_dtypes('number').columns))))

result['quality'] = dict(duplicateWithinYears=int(sum(df.duplicated().sum() for df in years.values())),duplicateAcrossCombined=int(all_data.duplicated(COLS).sum()),developmentUniqueInputs=int(len(dev.drop_duplicates(FEATURES))),comparisonInputsSeenInDevelopment=int(pd.MultiIndex.from_frame(comp[FEATURES]).isin(pd.MultiIndex.from_frame(dev[FEATURES])).sum()),constantColumns=[c for c in COLS if all_data[c].nunique()<=1],negativeCounts={c:int(all_data[c].lt(0).sum()) for c in COLS})
result['yearly'] = {col:[dict(year=int(y),count=len(df),mean=float(df[col].mean()),median=float(df[col].median()),std=float(df[col].std()),q1=float(df[col].quantile(.25)),q3=float(df[col].quantile(.75))) for y,df in years.items()] for col in COLS}
result['lag'] = {col:[dict(year=int(y),value=float(df[col].autocorr(lag=1))) for y,df in years.items()] for col in COLS}
result['sequence'] = {col:[dict(year=int(y),points=[dict(x=int(i),y=float(df[col].iloc[i])) for i in range(0,len(df),max(1,len(df)//180))]) for y,df in years.items()] for col in COLS}
for period, frame in [('development',dev),('2015',comp),('all',all_data)]:
    result['correlations'][period]={method:records(frame[COLS].corr(method=method).rename_axis('variable').reset_index()) for method in ['pearson','spearman']}
result['samples'] = records(all_data.iloc[::40][COLS+['Year']])
result['matrixPreview'] = records(dev[FEATURES].head(8))
result['targetPreview'] = records(dev[TARGETS].head(8))

std = dev[FEATURES].std(ddof=0)
Z = (dev[FEATURES]-dev[FEATURES].mean())/std
scale = []
for col in FEATURES:
    others=[c for c in FEATURES if c!=col]
    design=np.column_stack([np.ones(len(Z)), Z[others].to_numpy()])
    coef=np.linalg.lstsq(design,Z[col],rcond=None)[0]
    rss=np.sum((Z[col].to_numpy()-design@coef)**2)
    vif=float(np.sum(Z[col].to_numpy()**2)/rss)
    scale.append(dict(variable=col,mean=float(dev[col].mean()),scale=float(std[col]),median=float(dev[col].median()),minimum=float(dev[col].min()),maximum=float(dev[col].max()),vif=vif))
result['scaling']=scale
corr=dev[FEATURES].corr()
result['correlatedPairs']=sorted([dict(first=a,second=b,correlation=float(corr.loc[a,b])) for i,a in enumerate(FEATURES) for b in FEATURES[i+1:]],key=lambda r:abs(r['correlation']),reverse=True)

shift=[]
for col in COLS:
    d,c=dev[col],comp[col]
    below=int((c<d.min()).sum()); above=int((c>d.max()).sum())
    shift.append(dict(variable=col,developmentMean=float(d.mean()),comparisonMean=float(c.mean()),standardizedMeanDifference=float((c.mean()-d.mean())/d.std(ddof=0)),ks=float(ks_2samp(d,c).statistic),below=below,above=above,outsidePercent=float(100*(below+above)/len(c))))
result['shift']=sorted(shift,key=lambda r:r['ks'],reverse=True)
nearest=cKDTree(Z.to_numpy()).query(((comp[FEATURES]-dev[FEATURES].mean())/std).to_numpy(),k=1)[0]
result['jointCoverage']=dict(median=float(np.median(nearest)),p95=float(np.quantile(nearest,.95)),maximum=float(nearest.max()),description='Euclidean distance to the nearest development input row after development-fitted standardization. No safety or feasibility cutoff is applied.')

specs=[('TEY','outputs/random_forest_2015_predictions.csv','TEY_random_forest'),('CO','outputs/gradient_boosting_2015_predictions.csv','CO_gradient_boosting'),('NOX','outputs/baseline_2015_predictions.csv','NOX_linear_regression_pred')]
for target,file,key in specs:
    frame=read(file)
    actual=frame[target+'_actual'].to_numpy(); predicted=frame[key].to_numpy()
    assert np.allclose(actual,comp[target]), 'Prediction row alignment differs'
    residual=actual-predicted; absolute=np.abs(residual)
    summary=dict(target=target,n=len(actual),mae=float(absolute.mean()),rmse=float(np.sqrt(np.mean(residual**2))),r2=float(1-np.sum(residual**2)/np.sum((actual-actual.mean())**2)),meanResidual=float(residual.mean()),medianResidual=float(np.median(residual)),medianAE=float(np.median(absolute)),p90AE=float(np.quantile(absolute,.9)),p95AE=float(np.quantile(absolute,.95)),maxAE=float(absolute.max()),overPercent=float(100*np.mean(predicted>actual)),underPercent=float(100*np.mean(predicted<actual)))
    err_edges=np.linspace(residual.min(),residual.max(),33)
    by_range=[]
    groups=pd.qcut(actual,5,duplicates='drop')
    for group in groups.categories:
        mask=groups==group
        by_range.append(dict(label=f'{group.left:.2f} to {group.right:.2f}',count=int(mask.sum()),observedMean=float(actual[mask].mean()),predictedMean=float(predicted[mask].mean()),mae=float(absolute[mask].mean()),rmse=float(np.sqrt(np.mean(residual[mask]**2))),meanResidual=float(residual[mask].mean())))
    by_feature={}
    for feature in FEATURES:
        values=comp[feature].to_numpy(); groups=pd.qcut(values,5,duplicates='drop')
        rows=[]
        for group in groups.categories:
            mask=groups==group
            rows.append(dict(label=f'{group.left:.2f} to {group.right:.2f}',count=int(mask.sum()),featureMean=float(values[mask].mean()),mae=float(absolute[mask].mean()),meanResidual=float(residual[mask].mean())))
        by_feature[feature]=rows
    result['errors'][target]=dict(summary=summary,histogram=histogram(residual,err_edges),sample=[dict(actual=float(actual[i]),predicted=float(predicted[i]),residual=float(residual[i]),index=i) for i in range(0,len(actual),10)],byTargetRange=by_range,byFeature=by_feature)

result['splitComparison']=records(read('outputs/baseline_split_comparison.csv'))
result['methods']=dict(distributions='32 common equal-width bins per variable across all years; count and within-period percentages.',outliers='Values below Q1 - 1.5 IQR or above Q3 + 1.5 IQR within the selected period. Flags only; no rows removed.',correlations='Pearson linear correlation and Spearman rank correlation; select development, comparison or all observations.',vif='Ordinary least-squares regression of each standardized development input on the seven other inputs plus an intercept; VIF = 1/(1-R2). Diagnostic only, no feature removal.',shift='KS and standardized mean change compare 2011-2014 with 2015. Mean change is divided by development population standard deviation.',residuals='Observed minus predicted. Positive means underprediction; negative means overprediction. Summaries use all 7,384 saved comparison predictions.',errorBins='Five equal-frequency groups from 2015 actual target or input values. Used for retrospective diagnosis, not fitting or target leakage.',sampling='Scatter: every 40th combined data row; prediction/residual plots: every 10th comparison row; sequence: approximately 180 equally spaced rows per year. All summary statistics use full data.')
result['modelExplorers'] = {}
for target in TARGETS:
    result['modelExplorers'][target] = {}
    for name, file, suffix in [
        ('Mean Predictor','baseline','mean_predictor_pred'),
        ('Linear Regression','baseline','linear_regression_pred'),
        ('Ridge Regression','baseline','ridge_regression_pred'),
        ('Random Forest','random_forest','random_forest'),
        ('Gradient Boosting','gradient_boosting','gradient_boosting')]:
        frame = read(f'outputs/{file}_2015_predictions.csv')
        actual = frame[target+'_actual'].to_numpy()
        predicted = frame[target+'_'+suffix].to_numpy()
        assert np.allclose(actual, comp[target])
        residual = actual-predicted
        absolute = np.abs(residual)
        result['modelExplorers'][target][name] = dict(
            summary=dict(mae=float(absolute.mean()),rmse=float(np.sqrt(np.mean(residual**2))),meanResidual=float(residual.mean()),medianAE=float(np.median(absolute)),p90AE=float(np.quantile(absolute,.9)),p95AE=float(np.quantile(absolute,.95)),maxAE=float(absolute.max()),overPercent=float(100*np.mean(predicted>actual)),underPercent=float(100*np.mean(predicted<actual))),
            histogram=histogram(residual,np.linspace(residual.min(),residual.max(),33)),
            sample=[dict(actual=float(actual[i]),predicted=float(predicted[i]),residual=float(residual[i])) for i in range(0,len(actual),10)])
(OUT/'analysis.json').write_text(json.dumps(result,allow_nan=False,separators=(',',':')),encoding='utf-8')
print(json.dumps({'quality':result['quality'],'largestInputCorrelations':result['correlatedPairs'][:4],'VIF':scale,'shift':shift,'errors':[e['summary'] for e in result['errors'].values()]},indent=2))
