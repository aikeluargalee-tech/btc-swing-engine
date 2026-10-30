# DeepSeek API Integration Handoff Blueprint

Whenever you are ready to connect the DeepSeek API directly to the `btc_swing_engine`, simply copy-paste the activation prompt below into a new Antigravity session.

---

### Copy-Paste Activation Prompt for Antigravity

```markdown
Please proceed with the DeepSeek API Integration for the BTC Swing Engine (btc_swing_engine).

Context & Requirements:
1. Target Workspace: C:\Users\aikel\.gemini\antigravity\scratch\btc_swing_engine
2. Feature to Implement: Direct DeepSeek API background client (Mode 1: Hotkey 'A' on-demand AI audit).
3. API Configuration:
   - Provider: DeepSeek (https://api.deepseek.com/v1)
   - Preferred Model: deepseek-reasoner (DeepSeek-R1 CoT) or deepseek-chat (V3)
   - Read API key securely from .env (DEEPSEEK_API_KEY="sk-...")
4. Architecture Specifications:
   - Fully asynchronous & non-blocking: The WebSocket feeds (Binance Spot/Perp, Coinbase) and terminal HUD must NEVER stutter, freeze, or drop frames while DeepSeek is generating an audit.
   - Connects directly to `analytics/ai_packet_exporter.py` to transmit the compiled 11-section quantitative telemetry state.
   - Key 'A' triggers the audit on demand; key 'C' remains preserved for manual clipboard copying.
   - When the audit response arrives, render DeepSeek's structured verdict (Verdict, Conviction %, Critique of Benchmark, Reconciled Order of Battle, Plain-English Action) directly inside Tab [5: MASTER CONCLUSION] or a dedicated HUD panel.
   - Strictly adhere to the 5-Panel Single-Screen Law (<= 49 lines).
   - Run unit tests and a dry-run verification before completing.
```

---

### What to Have Ready When You Run This
1. Your DeepSeek API Key from [platform.deepseek.com](https://platform.deepseek.com) (`sk-...`).
2. That's it! Antigravity will handle all Python async wiring, HUD panels, and tests.
