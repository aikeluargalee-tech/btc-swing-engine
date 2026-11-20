"""One validated loader for every external file that can supply thresholds or claims.

Why this exists: three tabs each grew their own reader for a JSON/YAML file that a human
maintains, and each failed the same way — a missing, stale, corrupt or half-populated file
silently supplied the PERMISSIVE answer. Tab 2 reported "no liquidation cascade, risk LOW"
from a 24-day-old file; Tab A accepted `risk_per_trade: 0.05`; Tab M merged arbitrary keys
with `out.update(raw)`. Three bespoke validators, one defect.

Rules this module enforces, in one place:

1. **Absence is not permission.** A missing, unreadable or corrupt file yields UNAVAILABLE
   for every claim that depended on it. It never falls back to the favourable value.
2. **Age is part of validity.** A claim with a 72-hour window cannot be weeks old. Per-key
   maximum ages are enforced, and an unreadable or future timestamp invalidates the file.
3. **Unknown is UNAVAILABLE, not ignored.** An unrecognised value for an enumerated claim,
   or a number outside its declared bounds, is reported and dropped — not passed through.
4. **It never raises.** Callers render an operator-facing desk; a loader that throws takes the
   whole HUD down. Everything is returned in the result object.

The result carries `values`, `errors`, `age_hours` and a `status` the caller can display, so
the output can say *why* something is unavailable instead of showing a blank.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Optional, Sequence

UNAVAILABLE = "UNAVAILABLE"

STATUS_OK = "OK"
STATUS_MISSING = "MISSING"
STATUS_CORRUPT = "CORRUPT"
STATUS_STALE = "STALE"
STATUS_INVALID = "INVALID_TIMESTAMP"


@dataclass
class LoadedContext:
    """Validated view of one external file. `values` is always safe to index."""

    values: Dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    age_hours: Optional[float] = None
    status: str = STATUS_OK
    source_path: str = ""
    raw: Dict[str, Any] = field(default_factory=dict)   # parsed file, for non-claim keys

    @property
    def ok(self) -> bool:
        return self.status == STATUS_OK and not self.errors

    def reason(self) -> str:
        """One line explaining the state, for display next to the value."""
        if self.ok:
            age = f"{self.age_hours:.0f}h old" if self.age_hours is not None else "no age check"
            return f"{self.status} ({age})"
        detail = "; ".join(self.errors) if self.errors else "no detail"
        return f"{self.status}: {detail}"


def _parse_age_hours(raw_ts: Any) -> Optional[float]:
    """Parses an ISO-8601 UTC timestamp and returns its age. None if unusable."""
    if raw_ts is None:
        return None
    text = str(raw_ts).strip()
    if not text or text.upper() == UNAVAILABLE:
        return None
    try:
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    age = (datetime.now(timezone.utc) - dt.astimezone(timezone.utc)).total_seconds() / 3600.0
    return age


def validate_claims(
    raw: Mapping[str, Any],
    *,
    enumerated: Mapping[str, Iterable[str]],
    numeric: Optional[Mapping[str, tuple[float, float]]] = None,
    timestamp_key: str = "last_reviewed_utc",
    max_age_hours: Optional[Mapping[str, float]] = None,
    age_checked_keys: Optional[Sequence[str]] = None,
    default_age_hours: Optional[float] = None,
) -> LoadedContext:
    """Validates an already-parsed mapping. Pure: no file access, easy to test.

    enumerated       key -> permitted string values (case-insensitive on input)
    numeric          key -> (low, high) inclusive bounds
    timestamp_key    key holding the ISO review timestamp
    max_age_hours    per-key maximum age in hours
    age_checked_keys keys that inherit `default_age_hours` when no per-key limit is given
    """
    out = LoadedContext()
    numeric = numeric or {}
    max_age_hours = dict(max_age_hours or {})

    for key in set(enumerated) | set(numeric):
        out.values[key] = UNAVAILABLE

    age = _parse_age_hours(raw.get(timestamp_key))
    if age is None:
        out.status = STATUS_INVALID
        out.errors.append(f"{timestamp_key} missing, unreadable or in the future")
        return out
    if age < 0:
        out.status = STATUS_INVALID
        out.errors.append(f"{timestamp_key} is in the future")
        return out
    out.age_hours = age

    # Absence or age over a claim's own window makes that claim unavailable, per key.
    if age_checked_keys and default_age_hours is not None:
        for key in age_checked_keys:
            max_age_hours.setdefault(key, default_age_hours)

    stale_keys: list[str] = []
    for key, limit in max_age_hours.items():
        if age > float(limit):
            stale_keys.append(f"{key} age {age:.1f}h exceeds {float(limit):g}h")
    if stale_keys:
        out.status = STATUS_STALE
        out.errors.extend(stale_keys)

    for key, allowed in enumerated.items():
        if key in stale_keys or any(s.startswith(f"{key} ") for s in stale_keys):
            continue
        if key not in raw or raw.get(key) is None:
            out.errors.append(f"{key} missing")
            continue
        value = str(raw[key]).strip().upper()
        permitted = {str(a).strip().upper() for a in allowed}
        if value not in permitted:
            out.errors.append(f"{key}={raw[key]!r} not in {sorted(permitted)}")
            continue
        out.values[key] = value

    for key, (low, high) in numeric.items():
        if key not in raw or raw.get(key) is None:
            out.errors.append(f"{key} missing")
            continue
        try:
            num = float(raw[key])
        except (TypeError, ValueError):
            out.errors.append(f"{key}={raw[key]!r} is not a number")
            continue
        if not (low <= num <= high):
            out.errors.append(f"{key}={num:g} outside [{low:g}, {high:g}]")
            continue
        out.values[key] = num

    if out.status == STATUS_STALE:
        # A stale file invalidates the age-checked claims explicitly.
        for key in max_age_hours:
            out.values.setdefault(key, UNAVAILABLE)
            if any(s.startswith(f"{key} ") for s in stale_keys):
                out.values[key] = UNAVAILABLE

    return out


def load_claims_file(
    path: Optional[Path],
    *,
    enumerated: Mapping[str, Iterable[str]],
    numeric: Optional[Mapping[str, tuple[float, float]]] = None,
    timestamp_key: str = "last_reviewed_utc",
    max_age_hours: Optional[Mapping[str, float]] = None,
    age_checked_keys: Optional[Sequence[str]] = None,
    default_age_hours: Optional[float] = None,
) -> LoadedContext:
    """Reads and validates a JSON file. Missing/corrupt never raises and never permits."""
    if path is None:
        ctx = validate_claims({}, enumerated=enumerated, numeric=numeric,
                              timestamp_key=timestamp_key)
        ctx.status = STATUS_MISSING
        ctx.errors = ["no path configured"]
        return ctx

    p = Path(path)
    ctx_source = str(p)
    try:
        if not p.exists():
            ctx = validate_claims({}, enumerated=enumerated, numeric=numeric,
                                  timestamp_key=timestamp_key)
            ctx.status = STATUS_MISSING
            ctx.errors = [f"context file is missing: {p.name}"]
            ctx.source_path = ctx_source
            return ctx
        with open(p, "r", encoding="utf-8") as fh:
            raw = json.load(fh)
        if not isinstance(raw, dict):
            ctx = validate_claims({}, enumerated=enumerated, numeric=numeric,
                                  timestamp_key=timestamp_key)
            ctx.status = STATUS_CORRUPT
            ctx.errors = ["context root is not an object"]
            ctx.source_path = ctx_source
            return ctx
    except Exception as exc:
        ctx = validate_claims({}, enumerated=enumerated, numeric=numeric,
                              timestamp_key=timestamp_key)
        ctx.status = STATUS_CORRUPT
        ctx.errors = [f"context unreadable or corrupt ({type(exc).__name__})"]
        ctx.source_path = ctx_source
        return ctx

    ctx = validate_claims(
        raw,
        enumerated=enumerated,
        numeric=numeric,
        timestamp_key=timestamp_key,
        max_age_hours=max_age_hours,
        age_checked_keys=age_checked_keys,
        default_age_hours=default_age_hours,
    )
    ctx.source_path = ctx_source
    ctx.raw = dict(raw)
    return ctx
