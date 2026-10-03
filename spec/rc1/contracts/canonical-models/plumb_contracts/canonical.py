"""Canonical serialization and content digests.

Digest rule (DC-003): sha256 over UTF-8 of json.dumps(payload, sort_keys=True, separators=(",", ":"),
ensure_ascii=False) after removing every field named in EXCLUDED_FROM_DIGEST. Approvals and signatures
are detached, so a digest never includes a value that itself depends on the digest.
"""
import hashlib
import json
from typing import Any

EXCLUDED_FROM_DIGEST = {"content_digest", "manifest_digest", "approval_id", "signature", "approvals"}


def canonical_bytes(payload: dict[str, Any]) -> bytes:
    def strip(obj: Any) -> Any:
        if isinstance(obj, dict):
            return {k: strip(v) for k, v in obj.items() if k not in EXCLUDED_FROM_DIGEST}
        if isinstance(obj, list):
            return [strip(v) for v in obj]
        return obj

    return json.dumps(strip(payload), sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def digest(payload: dict[str, Any]) -> str:
    return "sha256:" + hashlib.sha256(canonical_bytes(payload)).hexdigest()
