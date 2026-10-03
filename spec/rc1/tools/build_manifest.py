"""Compute SHA-256 for every file in the package (excluding caches and the manifest itself)."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {"__pycache__", ".pytest_cache", ".hypothesis"}
entries = {}
for p in sorted(ROOT.rglob("*")):
    if p.is_dir() or any(part in SKIP_DIRS for part in p.parts) or p.name == "MANIFEST.json":
        continue
    rel = p.relative_to(ROOT).as_posix()
    entries[rel] = {"sha256": hashlib.sha256(p.read_bytes()).hexdigest(), "bytes": p.stat().st_size}
manifest = {"package": "plumb-spec", "version": "1.0.0-rc1", "file_count": len(entries), "files": entries}
(ROOT / "MANIFEST.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
print(f"manifest: {len(entries)} files")
