"""Validate source integrity, bundled links, data and optional HTTP hosting."""
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import sys
from urllib.parse import unquote, urljoin
from urllib.request import urlopen
ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT/'website'
class Links(HTMLParser):
    def __init__(self):
        super().__init__(); self.ids=[]; self.links=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if 'id' in a: self.ids.append(a['id'])
        for key in ['src','href']:
            if a.get(key): self.links.append(a[key])
p=Links();p.feed((SITE/'index.html').read_text(encoding='utf-8-sig'))
assert len(p.ids)==len(set(p.ids)), 'Duplicate IDs'
for link in p.links:
    if link.startswith('#'): assert link[1:] in p.ids,link
    elif not link.startswith(('https:','http:')):
        target=SITE/unquote(link)
        assert target.is_file() or (target/'index.html').is_file(),link
manifest=json.loads((SITE/'assets/data/provenance.json').read_text())
for path,digest in manifest['sources_sha256'].items():
    assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest,path
for notebook in (ROOT/'notebook').glob('*.ipynb'):
    copy=SITE/'assets/notebooks'/notebook.name
    if copy.exists():
        assert notebook.read_bytes()==copy.read_bytes()
d=json.loads((SITE/'assets/data/research.json').read_text())
assert sum(d['counts'].values())==36733
assert sum(c['Count'] for c in d['clusters'])==29349
assert len(d['pareto'])==56 and d['candidateCount']==29342
assert all(sum(b['y'] for b in h)==36733 for h in d['histograms'].values())
q=Links();q.feed((SITE/'predict/index.html').read_text(encoding='utf-8-sig'))
for link in q.links:
    if link.startswith('#'): assert link[1:] in q.ids,link
    elif not link.startswith(('https:','http:')):
        target=SITE/'predict'/unquote(link)
        assert target.is_file() or (target/'index.html').is_file(),link
assert 'Reproduce the experiments' not in (SITE/'index.html').read_text(encoding='utf-8-sig')
analysis=json.loads((SITE/'assets/data/analysis.json').read_text())
for source,digest in analysis['hashes'].items():
    assert hashlib.sha256((ROOT/source).read_bytes()).hexdigest()==digest,source
for period,values in analysis['periods'].items():
    for variable,histogram in values['histograms'].items():
        assert sum(row['y'] for row in histogram)==values['rows'],(period,variable)
        assert abs(sum(row['percent'] for row in histogram)-100)<1e-8
for target,error in analysis['errors'].items():
    reference=next(row for row in d['selected'] if row['Prediction target']==target)
    for new,old in [('mae','MAE'),('rmse','RMSE'),('r2','R-squared')]:
        assert abs(error['summary'][new]-reference[old])<1e-10,(target,new)
    assert sum(row['count'] for row in error['byTargetRange'])==7384
    for rows in error['byFeature'].values():
        assert sum(row['count'] for row in rows)==7384
for target,models in analysis['modelExplorers'].items():
    assert len(models)==5
    for name,error in models.items():
        reference=next(row for row in d['models'] if row['Target']==target and row['Model']==name)
        for metric in ['mae','rmse']:
            assert abs(error['summary'][metric]-reference[metric.upper()])<1e-10,(target,name,metric)
        assert sum(row['y'] for row in error['histogram'])==7384
refs=json.loads((SITE/'assets/data/references.json').read_text())
assert len(refs)==28
for ref in refs:
    assert f'ref-{ref["number"]}' in p.ids
    assert ref['url'] in (SITE/'index.html').read_text(encoding='utf-8')
for section in ['research-question','source-files','data-quality','preprocessing','model-selection',
                'evaluation-design','final-results','residual-analysis','operating-regimes',
                'nox-investigation','prediction-tradeoffs','prediction-explorer','limitations','reproducibility']:
    assert section in p.ids
for file in ['index.html','predict/index.html']:
    contents=(SITE/file).read_text(encoding='utf-8-sig')
    assert '\ufffd' not in contents, file
    for removed in ['class="eyebrow"','class="section-nav"','Runs privately in your browser','GAS TURBINE','brandmark']:
        assert removed not in contents,(file,removed)
assert (SITE/'index.html').read_text().count('class="sidebar-group"')==3
print('PASS: detailed-analysis source hashes, histogram totals, full-data error metrics, bin counts, three sidebar groups and plain interface text.')
if len(sys.argv)>1:
    base=sys.argv[1]
    for path in [SITE/'index.html',SITE/'predict/index.html',SITE/'404.html',*(SITE/'assets').rglob('*')]:
        if path.is_file():
            with urlopen(urljoin(base,path.relative_to(SITE).as_posix())) as r:
                assert r.status==200
                assert r.read()==path.read_bytes(),path
    print('HTTP: all bundled assets and pages returned 200 at',base)
print(f'PASS: {len(p.ids)} unique IDs, {len(p.links)} links, {len(manifest["sources_sha256"])} source hashes, available notebook copies and data invariants.')
