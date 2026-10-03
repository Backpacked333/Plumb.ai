"""Generate JSON Schema (draft 2020-12) for every top-level canonical model.

Run: python tools/gen_schemas.py   (from the package root)
Output: contracts/generated-json-schema/<Model>.schema.json plus index.json
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "contracts" / "canonical-models"))

from plumb_contracts.models import TOP_LEVEL_MODELS  # noqa: E402

OUT = ROOT / "contracts" / "generated-json-schema"
OUT.mkdir(parents=True, exist_ok=True)
index = {}
for name, model in TOP_LEVEL_MODELS.items():
    schema = model.model_json_schema(mode="validation")
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["$id"] = f"https://plumb.example/schemas/{name}.schema.json"
    path = OUT / f"{name}.schema.json"
    path.write_text(json.dumps(schema, indent=2, sort_keys=True) + "\n")
    index[name] = path.name
(OUT / "index.json").write_text(json.dumps(index, indent=2, sort_keys=True) + "\n")
print(f"generated {len(index)} schemas into {OUT}")
