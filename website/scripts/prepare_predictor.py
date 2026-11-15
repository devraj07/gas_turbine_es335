"""Prepare audits and browser models without changing research source files."""
from pathlib import Path
import csv,json,hashlib
import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import RandomForestRegressor,GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error,mean_squared_error,r2_score
ROOT=Path(__file__).resolve().parents[2]; OUT=ROOT/'website/assets/data'
features=['AT','AP','AH','AFDP','GTEP','TIT','TAT','CDP']; targets=['TEY','CO','NOX']
frames={str(y):pd.read_csv(ROOT/f'data/gt_{y}.csv') for y in range(2011,2016)}
def audit(df):
 stats=[]
 for col in features+targets:
  s=df[col]; stats.append(dict(variable=col,role='Input' if col in features else 'Target',count=int(s.count()),missing=int(s.isna().sum()),missingPercent=float(s.isna().mean()*100),mean=float(s.mean()),median=float(s.median()),std=float(s.std()),min=float(s.min()),max=float(s.max())))
 return dict(rows=len(df),missing=int(df.isna().sum().sum()),duplicates=int(df.duplicated().sum()),infinite=int(np.isinf(df.select_dtypes('number')).sum().sum()),statistics=stats)
all_data=pd.concat(frames.values(),ignore_index=True)
audits={year:audit(df) for year,df in frames.items()};audits['all']=audit(all_data)
inventory=[]
for p in sorted((ROOT/'outputs').rglob('*.csv')):
 rows=list(csv.reader(p.open(encoding='utf-8-sig')))
 multi=len(rows)>2 and rows[1][0]=='' and any(x in ['mean','count','std'] for x in rows[1])
 inventory.append(dict(file=p.relative_to(ROOT).as_posix(),rows=len(rows)-(3 if multi else 1),columns=len(rows[0]),fields=list(dict.fromkeys(x for x in rows[0] if x)),group=p.parent.name if p.parent.name!='outputs' else 'Core results'))
(OUT/'audit.json').write_text(json.dumps(dict(periods=audits,files=inventory),allow_nan=False,separators=(',',':')),encoding='utf-8')
train=pd.concat([frames[str(y)] for y in range(2011,2015)],ignore_index=True); X=train[features]; test=frames['2015']
models={
 'TEY':RandomForestRegressor(n_estimators=100,max_depth=15,min_samples_split=5,min_samples_leaf=2,max_features=1.0,random_state=42,n_jobs=1),
 'CO':GradientBoostingRegressor(n_estimators=100,learning_rate=.05,max_depth=2,min_samples_split=5,min_samples_leaf=2,subsample=.8,loss='squared_error',random_state=42),
 'NOX':LinearRegression()}
def tree(m):
 t=m.tree_
 return dict(left=t.children_left.tolist(),right=t.children_right.tolist(),feature=t.feature.tolist(),threshold=t.threshold.tolist(),value=t.value[:,0,0].tolist())
export=dict(features=features,ranges={f:dict(min=float(X[f].min()),max=float(X[f].max()),default=float(X[f].median())) for f in features},models={},sklearn=sklearn.__version__,trainingRows=len(X),evaluation={})
fixtures=[]
for name,m in models.items():
 print('Fitting',name,flush=True);m.fit(X,train[name]);pred=m.predict(test[features]);export['evaluation'][name]=dict(MAE=float(mean_absolute_error(test[name],pred)),RMSE=float(np.sqrt(mean_squared_error(test[name],pred))),R2=float(r2_score(test[name],pred)))
 if name=='TEY': export['models'][name]=dict(kind='forest',trees=[tree(t) for t in m.estimators_])
 elif name=='CO': export['models'][name]=dict(kind='boosting',base=float(m.init_.constant_[0,0]),rate=m.learning_rate,trees=[tree(t[0]) for t in m.estimators_])
 else: export['models'][name]=dict(kind='linear',intercept=float(m.intercept_),coefficients=m.coef_.tolist())
for _,row in test.iloc[::150].iterrows():
 x=row[features].to_frame().T
 fixtures.append(dict(input=row[features].tolist(),expected={t:float(m.predict(x)[0]) for t,m in models.items()}))
(OUT/'browser-models.json').write_text(json.dumps(export,allow_nan=False,separators=(',',':')),encoding='utf-8')
(OUT/'prediction-fixtures.json').write_text(json.dumps(fixtures,separators=(',',':')),encoding='utf-8')
print(json.dumps(export['evaluation'],indent=2));print('Export bytes:',(OUT/'browser-models.json').stat().st_size)

