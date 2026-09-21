"""Package only the explicit public website and GitHub Pages configuration."""
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / 'site'
OUTPUT = ROOT / 'outputs' / 'github-pages'
FILES = [
    '.github/workflows/deploy-pages.yml', '.gitignore', 'README.md',
    'dist/index.html', 'dist/style.css', 'dist/app.js', 'dist/core.js', 'dist/chemical-ui.js',
    *[f'dist/data/{name}.json' for name in (
        'achievements', 'activities', 'textbooks', 'materials', 'quantities', 'chemicals', 'chemical_guidelines', 'sources')],
]

def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    archive = OUTPUT / 'science-classroom-prep-github-pages.zip'
    temporary = archive.with_suffix('.zip.tmp')
    with ZipFile(temporary, 'w', compression=ZIP_DEFLATED) as bundle:
        for name in FILES:
            source = SITE / name
            assert source.is_file() and not source.is_symlink(), f'Missing regular file: {name}'
            assert source.resolve().is_relative_to(SITE.resolve()), f'File outside site: {name}'
            bundle.write(source, name)
    with ZipFile(temporary) as bundle:
        assert bundle.testzip() is None
        assert set(bundle.namelist()) == set(FILES)
        for name in FILES:
            assert bundle.read(name) == (SITE / name).read_bytes(), f'Content mismatch: {name}'
    temporary.replace(archive)
    report = {'archive': str(archive), 'files': FILES, 'file_count': len(FILES),
              'bytes': archive.stat().st_size,
              'sha256': hashlib.sha256(archive.read_bytes()).hexdigest()}
    (OUTPUT / 'package-manifest.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
