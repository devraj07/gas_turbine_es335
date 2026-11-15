"""Package only deployable assets: python website/scripts/package_site.py."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import unquote
import shutil

ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT / 'website'
DEST = ROOT / '.pages'
FILES = [
    'index.html', 'predict/index.html', '404.html', '.nojekyll',
    'assets/turbine-icon.svg', 'assets/css/style.css',
    'assets/js/app.js', 'assets/js/predict.js', 'assets/js/inference.js',
    'assets/data/analysis.json', 'assets/data/research.json', 'assets/data/notebook-methods.json', 'assets/data/references.json',
    'assets/data/audit.json', 'assets/data/provenance.json',
    'assets/data/browser-models.json', 'assets/data/all_models_comparison.csv',
]

# Only this generated workspace directory can be replaced.
if DEST.is_symlink() or DEST.resolve() != ROOT.resolve() / '.pages':
    raise RuntimeError('Refusing to replace an unexpected staging path')
if DEST.exists():
    shutil.rmtree(DEST)
DEST.mkdir()
for name in FILES:
    target = DEST / name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(SITE / name, target)

# Original notebooks have one tracked location; download copies exist only in the artifact.
notebooks = sorted((ROOT / 'notebook').glob('*.ipynb'))
assert len(notebooks) == 12
for notebook in notebooks:
    target = DEST / 'assets/notebooks' / notebook.name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(notebook, target)

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if key in ('href', 'src') and value:
                self.links.append(value)

for page in [DEST / 'index.html', DEST / 'predict/index.html']:
    parser = Links()
    parser.feed(page.read_text(encoding='utf-8-sig'))
    for link in parser.links:
        if link.startswith(('#', 'https:', 'http:')):
            continue
        target = page.parent / unquote(link)
        assert target.is_file() or (target / 'index.html').is_file(), (page, link)
files = [p for p in DEST.rglob('*') if p.is_file()]
assert not any(p.name.lower().startswith('readme') or p.suffix == '.zip' for p in files)
assert not (DEST / 'scripts').exists()
print(f'Packaged {len(files)} files ({sum(p.stat().st_size for p in files)/1e6:.1f} MB) in {DEST}')
