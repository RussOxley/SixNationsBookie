from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Dict, Any

@dataclass(frozen=True)
class PriorCommitment:
    user_id: str
    commitment_hash: str

def commit_prior(user_id: str, prior_payload: Dict[str, Any], salt: str) -> PriorCommitment:
    blob = json.dumps(prior_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    msg = blob + ("|" + salt).encode("utf-8")
    h = hashlib.sha256(msg).hexdigest()
    return PriorCommitment(user_id=user_id, commitment_hash=h)

def verify_reveal(commitment_hash: str, prior_payload: Dict[str, Any], salt: str) -> bool:
    blob = json.dumps(prior_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    msg = blob + ("|" + salt).encode("utf-8")
    h = hashlib.sha256(msg).hexdigest()
    return h == commitment_hash
