"""Tests for the single validated context loader.

These assert the rule that matters: an absent, stale, corrupt or half-populated file must
never supply the permissive answer.
"""
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from core.context_loader import (
    STATUS_CORRUPT,
    STATUS_INVALID,
    STATUS_MISSING,
    STATUS_OK,
    STATUS_STALE,
    UNAVAILABLE,
    load_claims_file,
    validate_claims,
)

ENUM = {
    "liq_cascade_72h_over_300m": ["TRIGGERED", "CONFIRMED_CLEAR"],
    "s2_risk_level": ["LOW", "MED", "HIGH"],
}


def _fresh(hours_ago: float = 1.0) -> str:
    ts = datetime.now(timezone.utc) - timedelta(hours=hours_ago)
    return ts.strftime("%Y-%m-%dT%H:%M:%SZ")


class TestValidatedContext(unittest.TestCase):
    def test_missing_file_is_unavailable_not_clear(self):
        p = Path(tempfile.gettempdir()) / "definitely_not_here_ctx.json"
        if p.exists():
            p.unlink()
        ctx = load_claims_file(p, enumerated=ENUM)
        self.assertEqual(ctx.status, STATUS_MISSING)
        self.assertFalse(ctx.ok)
        for key in ENUM:
            self.assertEqual(ctx.values[key], UNAVAILABLE)

    def test_corrupt_file_is_unavailable(self):
        p = Path(tempfile.gettempdir()) / "corrupt_ctx_test.json"
        p.write_text("{not valid json", encoding="utf-8")
        ctx = load_claims_file(p, enumerated=ENUM)
        self.assertEqual(ctx.status, STATUS_CORRUPT)
        self.assertEqual(ctx.values["liq_cascade_72h_over_300m"], UNAVAILABLE)

    def test_stale_file_invalidates_its_claims(self):
        p = Path(tempfile.gettempdir()) / "stale_ctx_test.json"
        p.write_text(json.dumps({
            "last_reviewed_utc": _fresh(hours_ago=500),
            "liq_cascade_72h_over_300m": "CONFIRMED_CLEAR",
            "s2_risk_level": "LOW",
        }), encoding="utf-8")
        ctx = load_claims_file(p, enumerated=ENUM,
                               max_age_hours={"liq_cascade_72h_over_300m": 72.0,
                                              "s2_risk_level": 24.0})
        self.assertEqual(ctx.status, STATUS_STALE)
        self.assertEqual(ctx.values["liq_cascade_72h_over_300m"], UNAVAILABLE)
        self.assertIn("exceeds", " ".join(ctx.errors))

    def test_future_timestamp_is_invalid(self):
        p = Path(tempfile.gettempdir()) / "future_ctx_test.json"
        future = (datetime.now(timezone.utc) + timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
        p.write_text(json.dumps({"last_reviewed_utc": future,
                                 "liq_cascade_72h_over_300m": "CONFIRMED_CLEAR",
                                 "s2_risk_level": "LOW"}), encoding="utf-8")
        ctx = load_claims_file(p, enumerated=ENUM)
        self.assertEqual(ctx.status, STATUS_INVALID)
        self.assertEqual(ctx.values["s2_risk_level"], UNAVAILABLE)

    def test_unknown_enum_value_is_rejected_not_passed_through(self):
        ctx = validate_claims(
            {"last_reviewed_utc": _fresh(), "liq_cascade_72h_over_300m": "PROBABLY_FINE",
             "s2_risk_level": "LOW"},
            enumerated=ENUM)
        self.assertEqual(ctx.values["liq_cascade_72h_over_300m"], UNAVAILABLE)
        self.assertEqual(ctx.values["s2_risk_level"], "LOW")
        self.assertTrue(any("not in" in e for e in ctx.errors))

    def test_numeric_bounds_reject_out_of_range(self):
        ctx = validate_claims(
            {"last_reviewed_utc": _fresh(), "cycle_ath_override_usd": 1.0},
            enumerated={}, numeric={"cycle_ath_override_usd": (10_000.0, 500_000.0)})
        self.assertEqual(ctx.values["cycle_ath_override_usd"], UNAVAILABLE)
        self.assertTrue(any("outside" in e for e in ctx.errors))

    def test_valid_fresh_file_is_ok(self):
        p = Path(tempfile.gettempdir()) / "good_ctx_test.json"
        p.write_text(json.dumps({
            "last_reviewed_utc": _fresh(hours_ago=2),
            "liq_cascade_72h_over_300m": "CONFIRMED_CLEAR",
            "s2_risk_level": "LOW",
        }), encoding="utf-8")
        ctx = load_claims_file(p, enumerated=ENUM,
                               max_age_hours={"liq_cascade_72h_over_300m": 72.0,
                                              "s2_risk_level": 24.0})
        self.assertTrue(ctx.ok, ctx.reason())
        self.assertEqual(ctx.values["liq_cascade_72h_over_300m"], "CONFIRMED_CLEAR")
        assert ctx.age_hours is not None
        self.assertLess(ctx.age_hours, 24.0)

    def test_boolean_is_not_accepted_where_a_number_belongs(self):
        # bool subclasses int; float(True) == 1.0 would silently turn a flag into a price.
        ctx = validate_claims(
            {"last_reviewed_utc": _fresh(), "price": True},
            enumerated={}, numeric={"price": (0.0, 1_000_000.0)})
        self.assertEqual(ctx.values["price"], UNAVAILABLE)
        self.assertTrue(any("boolean" in e for e in ctx.errors))

    def test_optional_timestamp_validates_values_but_reports_the_gap(self):
        # Override files carry values, not review assertions: a missing date is reported,
        # not fatal, and staleness is still enforced when a date IS present.
        ctx = validate_claims(
            {"price": 108_000.0},
            enumerated={}, numeric={"price": (0.0, 1_000_000.0)},
            age_checked_keys=["price"], default_age_hours=72.0,
            require_timestamp=False)
        self.assertEqual(ctx.values["price"], 108_000.0)
        self.assertIsNone(ctx.age_hours)
        self.assertTrue(any("age" in e for e in ctx.errors))

    def test_never_raises_on_garbage(self):
        for bad in ({}, {"last_reviewed_utc": None}, {"last_reviewed_utc": "not-a-date"},
                    {"last_reviewed_utc": ""}):
            ctx = validate_claims(bad, enumerated=ENUM)
            self.assertFalse(ctx.ok)
            self.assertEqual(ctx.values["s2_risk_level"], UNAVAILABLE)


if __name__ == "__main__":
    unittest.main()
