"""Repo-wide invariants. These exist so a fixed bug class cannot come back.

Each test scans source for a pattern that has already caused a real defect in this
repo, and fails unless the occurrence is in a documented allowlist. Adding an entry
to an allowlist is a deliberate act with a stated reason - not a way to silence the
check.

Defects these guard against (all found in Tabs P, Q and W):
  * a gate defaulting to PERMISSION when telemetry is missing
  * risk arithmetic that silently assumes a $100k account
  * output that claims a trade is authorised, when nothing in this stack may authorise
"""

from __future__ import annotations

import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCAN_DIRS = ["analytics", "ui"]
SKIP_DIRS = {".venv", "__pycache__", ".git", "node_modules"}


def py_files() -> list[pathlib.Path]:
    out: list[pathlib.Path] = []
    for d in SCAN_DIRS:
        base = ROOT / d
        if not base.exists():
            continue
        for p in base.rglob("*.py"):
            if any(part in SKIP_DIRS for part in p.parts):
                continue
            out.append(p)
    return out


def scan(pattern: str) -> list[tuple[str, int, str]]:
    rx = re.compile(pattern)
    hits = []
    for f in py_files():
        for i, line in enumerate(f.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
            if line.lstrip().startswith("#"):
                continue
            if rx.search(line):
                hits.append((str(f.relative_to(ROOT)).replace("\\", "/"), i, line.strip()))
    return hits


class TestNoFailOpenGates(unittest.TestCase):
    """A gate must never default to the permissive answer."""

    # (file, substring that identifies the line, why it is acceptable)
    ALLOWED = [
        ("analytics/strategy_trend_pullback.py", 'getattr(b, "is_closed", True)',
         "redundant: the next line rejects forming bars on timestamp_ms + tf_ms <= now_ms"),
    ]

    def test_no_getattr_default_true_in_gates(self):
        hits = scan(r"getattr\([^)]*,\s*True\s*\)")
        unexpected = []
        for rel, line_no, text in hits:
            if any(rel == a[0] and a[1] in text for a in self.ALLOWED):
                continue
            unexpected.append(f"{rel}:{line_no}: {text[:100]}")
        self.assertEqual(
            [], unexpected,
            "fail-open gate default(s) found - a missing field must never read as PASS:\n  "
            + "\n  ".join(unexpected),
        )


class TestNoHardcodedEquityInArithmetic(unittest.TestCase):
    """Risk numbers must derive from configured equity, never a literal account size."""

    def test_no_literal_equity_in_risk_arithmetic(self):
        """A literal account size used as an OPERAND in a risk calculation.

        Deliberately narrow. A config read with a fallback
        (`getattr(config, "portfolio_equity_usd", 100_000.0)`) and a dataclass field
        default are not this defect - the value is supplied at runtime. The defect is a
        literal multiplying a risk fraction, which produces a number that ignores the
        real account (the exported Tab P packet printed Max Risk from a bare 100000.0
        while the size beside it used the configured equity).
        """
        operand = re.compile(r"100_?000(?:\.0)?\s*\*|\*\s*100_?000(?:\.0)?")
        offenders = []
        for rel, ln, text in scan(r"100_?000(?:\.0)?"):
            if "100_000_000" in text:
                continue
            if not operand.search(text):
                continue
            if not re.search(r"risk|equity|account", text, re.I):
                continue
            if re.search(r"math\.floor|round\(", text):
                continue          # unit scaling / quantity rounding, not an account size
            offenders.append(f"{rel}:{ln}: {text[:110]}")
        self.assertEqual([], offenders,
                         "literal equity used in risk arithmetic:\n  " + "\n  ".join(offenders))


class TestNothingMayAuthoriseATrade(unittest.TestCase):
    """The stack is veto-only. No artefact may claim authority to execute."""

    ALLOWED = [
        ("analytics/reconciliation_engine.py", "execution_authorization",
         "field name and machine value only; it is never rendered. The gate is displayed "
         "through format_data_integrity_lock(), which prints a LOCK state, because the raw "
         "value can be AUTHORIZED and that word must never reach an artefact."),
        ("analytics/reconciliation_engine.py", "Execution Authorization",
         "report label for the data-integrity gate above"),
        ("analytics/slsp_engine.py", "execution_authorization",
         "reads the gate; only the DENIED branch acts"),
        ("analytics/btc_magnet_engine.py", "reconciliation_auth",
         "passes the gate through, never uses it to permit"),
        ("analytics/four_gate_engine.py", "execution_authorization",
         "reads the gate for the data-integrity status line"),
        ("ui/terminal_hud.py", "AUTHORIZED",
         "renders the gate's own status text"),
        ("analytics/data_only_reports.py", 'replace("EXECUTION AUTHORIZED"',
         "strips the phrase from the output; it cannot emit it"),
    ]

    def test_no_execute_authorisation_claims(self):
        hits = scan(r"EXECUTION AUTHORIZED|EXECUTION_AUTHORIZED|Execution Authorization")
        offenders = []
        for rel, ln, text in hits:
            if any(rel == a[0] and a[1] in text for a in self.ALLOWED):
                continue
            offenders.append(f"{rel}:{ln}: {text[:100]}")
        self.assertEqual([], offenders,
                         "an artefact claims execution authority:\n  " + "\n  ".join(offenders))


if __name__ == "__main__":
    unittest.main()
