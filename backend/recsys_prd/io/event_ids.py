from __future__ import annotations

import hashlib


def build_event_id(*parts: str) -> str:
    """Build a deterministic event identifier from stable parts."""
    raw_key = "|".join(parts)
    return hashlib.sha1(raw_key.encode("utf-8")).hexdigest()
