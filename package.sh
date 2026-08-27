#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
python3 - "$ROOT" <<'PY'
from __future__ import annotations

import json
import sys
import zipfile
from pathlib import Path

root = Path(sys.argv[1]).resolve()
manifest = json.loads((root / "module.json").read_text(encoding="utf-8"))
module_id = manifest["id"]
version = manifest["version"]
dist = root / "dist"
dist.mkdir(exist_ok=True)
archive_path = dist / f"{module_id}-{version}.zip"

exclude_names = {
    "LICENSE.md",
    "compose-assets.py",
}
exclude_dirs = {"dist", "tests", ".git", "__pycache__"}
exclude_prefixes = {("assets", "sources")}
exclude_suffixes = {".pyc", ".tar.gz"}

if archive_path.exists():
    archive_path.unlink()

with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if relative.parts and relative.parts[0] in exclude_dirs:
            continue
        if relative.parts[:2] in exclude_prefixes:
            continue
        if relative.name in exclude_names:
            continue
        if relative.suffix in exclude_suffixes:
            continue
        archive.write(path, f"{module_id}/{relative.as_posix()}")

print(archive_path)
PY
