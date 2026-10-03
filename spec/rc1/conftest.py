import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
for p in [
    ROOT / "contracts" / "canonical-models",
    ROOT / "reference" / "bounded-plan-validator",
    ROOT / "reference" / "guarded-state-transitions",
    ROOT / "reference" / "effect-protocol-harness",
    ROOT / "reference" / "policy-gateway",
    ROOT / "reference" / "collector-convergence",
]:
    sys.path.insert(0, str(p))
