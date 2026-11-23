"""Create the small reader/lab archive; Git history stays in the repository."""

from pathlib import Path
import json
import sys
import zipfile


ROOT = Path(__file__).resolve().parents[1]
DEFAULT = ROOT / 'dist' / 'llm-manual-lab.zip'
target = Path(sys.argv[1]).expanduser().resolve() if len(sys.argv) > 1 else DEFAULT
target.parent.mkdir(parents=True, exist_ok=True)


def included(path: Path) -> bool:
    rel = path.relative_to(ROOT)
    if any(part in {'.git', '.venv', '.venv-tokenizer', 'node_modules',
                    '__pycache__', '.pytest_cache', 'dist', 'work'} for part in rel.parts):
        return False
    if rel.parts[:2] == ('manual', 'out'):
        return False
    return path.name != '.DS_Store'


files = sorted(path for path in ROOT.rglob('*') if path.is_file() and included(path))
with zipfile.ZipFile(target, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
    for path in files:
        archive.write(path, 'llm-manual-lab/' + path.relative_to(ROOT).as_posix())

with zipfile.ZipFile(target) as archive:
    assert archive.testzip() is None
    assert len(archive.namelist()) == len(files)
    assert not any('/.git/' in name for name in archive.namelist())

print(json.dumps({'archive': str(target), 'files': len(files),
                  'bytes': target.stat().st_size}, ensure_ascii=False))
