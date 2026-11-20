# AGENTS.md — rules for any agent working in this repo

This file exists because four different agents (Antigravity, Codex, OpenCode, Milo1)
have worked here, each re-deriving the conventions and each introducing its own style
of mistake. Read this before editing anything.

---

## 1. Non-negotiable invariants

These three are enforced by `tests/test_invariants.py`. If your change fails that file,
the change is wrong — not the test.

### Gates fail CLOSED

A gate, veto, permission or risk check must never default to the permissive answer when
telemetry is missing.

```python
getattr(obj, "above_200d_sma", True)     # WRONG: missing data reads as PASS
getattr(obj, "above_200d_sma", False)    # right
```

This was found six times in one sweep (Tabs F, W and the HUD). The worst case was
`post_flush_stabilized` defaulting True, which disarmed the cascade veto precisely during
an active liquidation flush with unknown state — the moment it was needed.

### Risk arithmetic reads configured equity

Never a literal account size.

```python
risk = 100000.0 * (risk_pct / 100)                   # WRONG
risk = config.portfolio_equity_usd * (risk_pct / 100)  # right
```

A config read with a fallback is fine (`getattr(config, "portfolio_equity_usd", 100_000.0)`);
a literal multiplying a risk fraction is not. The exported Tab P packet once printed
"Max Risk" from a bare `100000.0` while the position size beside it used the real equity —
two numbers in one line that disagreed.

### Nothing may authorise a trade

This stack is **veto-only**. Every component can subtract (pause, shrink, widen, refuse).
None may add. If you write output containing "EXECUTION AUTHORIZED", "GO", or a statement
that a trade is permitted, you have broken the architecture.

A preflight passing is **not** permission — it only removes one objection.

---

## 2. Reporting conventions

**A published number must recompute from the numbers beside it.** If a score is a mean of
desk points, publish the mean. Tab L applied `max(raw, 75.0)` under a "3+ green" condition,
so 65.6 printed as 75.0 and could cross a `>= 70` gate on its own.

**Labels must state the threshold actually used.** Tab P's report said "(<= 4.5%)" while the
engine tested 4.8 — the value passed a check it did not pass.

**A label must describe what the code does.** Tab P called its stop "(1H Close)" while
nothing read a 1-hour close.

**Never print an instruction next to a non-action.** Tab Q printed
`Execution Ticket: Deploy $10,000` under a verdict of `STANDBY`. Gate it on the gate count.

**The export must match the screen.** Tab W's HUD and its exported report each computed
their own five pillars, from different fields. Reviewers were auditing a model that did not
exist. When a value is computed in two places, extract it to one function and have both read
that function.

**A missing value is `UNAVAILABLE`. An invented one is a defect.** This includes
distributions where a single value is not meaningful: the 30D volume profile is bimodal, so
it reports `BIMODAL (Peaks: …)` rather than a confident band.

---

## 3. How to work here

- **Run the suite before and after.** `.venv\Scripts\python.exe -m pytest tests -q`. A
  broken test is a broken change.
- **Never loosen a threshold or a guard to make a test pass.** If a guard fires, the code
  under it is wrong. If a guard is genuinely wrong, change it deliberately and say why in
  the commit message.
- **Never delete a fail-closed default to silence a warning.** Set it to the conservative
  value and explain in a comment what the missing data means.
- **Check `git status` first.** Other agents work in this same checkout. Do not commit
  files another agent is mid-way through editing, and do not `git add -A` — commit explicit
  paths.
- **Do not touch unrelated tabs.** One tab or one defect class per change.
- **State what you measured.** "Tests pass" is a claim; paste the count. "Fixed" is a claim;
  show the output that changed.

---

## 4. Allowlist policy

`tests/test_invariants.py` carries short allowlists. Each entry names the file, the exact
text, and **why it is acceptable**. Adding an entry is a deliberate act with a written
reason. It is not a way to quiet the check — if you cannot say why an occurrence is safe in
one line, the occurrence is a defect.

---

## 5. Known deliberate limitations

- The volume profile watches the committed feed, not GitHub Pages, to avoid cache lag.
  A CDN failure after a good publish is therefore not detected here.
- `strategy_trend_pullback` reads `getattr(b, "is_closed", True)` in two places. This is
  safe only because the next line rejects forming bars on `timestamp_ms + tf_ms <= now_ms`.
  Do not remove that timestamp check.
- The `execution_authorization` field exists in the reconciliation gate. It is only ever
  read as `DENIED` (a lock). It must never be read as permission.
