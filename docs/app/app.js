(function () {
  "use strict";

  const state = {
    payload: null,
    tier: "pro", // "pro" | "free"
    activeTab: "desk",
    panelFilter: "all",
    searchQuery: "",
    selectedPlan: "annual"
  };

  function esc(str) {
    return String(str == null ? "" : str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function showToast(msg) {
    const el = document.getElementById("toast");
    if (!el) return;
    el.textContent = msg;
    el.classList.add("show");
    clearTimeout(showToast._t);
    showToast._t = setTimeout(() => el.classList.remove("show"), 2200);
  }

  function findRow(payload, labelPrefix) {
    const panels = (payload && payload.panels) || {};
    for (const key of Object.keys(panels)) {
      const rows = (panels[key] && panels[key].rows) || [];
      for (const r of rows) {
        if (String(r.label || "").indexOf(labelPrefix) !== -1) return r;
      }
    }
    return null;
  }

  function extractHeaderField(md, regex) {
    const m = regex.exec(String(md || ""));
    return m ? m[1] : "";
  }

  function calcAgeMinutes(utcStr) {
    const m = /^(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2}:\d{2})\s+UTC$/.exec(String(utcStr || "").trim());
    if (!m) return null;
    const ts = Date.parse(m[1] + "T" + m[2] + "Z");
    if (!isFinite(ts)) return null;
    return Math.max(0, Math.floor((Date.now() - ts) / 60000));
  }

  function statusPill(status) {
    const st = String(status || "UNAVAILABLE").toUpperCase();
    if (st === "OK") return `<span class="pill pill-green">OK</span>`;
    if (st === "PROXY") return `<span class="pill pill-amber">PROXY</span>`;
    if (st === "STALE") return `<span class="pill pill-blue">STALE</span>`;
    return `<span class="pill pill-red">N/A</span>`;
  }

  function renderHeader(payload) {
    const mins = calcAgeMinutes(payload.retrieval_utc);
    const dotEl = document.getElementById("hdr-live-dot");
    const subEl = document.getElementById("hdr-age-text");
    if (mins == null) {
      subEl.textContent = payload.retrieval_sgt || "Snapshot loaded";
    } else {
      dotEl.className = "live-dot" + (mins > 90 ? " stale" : mins > 70 ? " warn" : "");
      subEl.textContent = `Updated ${mins}m ago · ${payload.retrieval_sgt || payload.retrieval_utc}`;
    }

    const tierBtn = document.getElementById("tier-toggle-btn");
    const isPro = state.tier === "pro";
    tierBtn.textContent = isPro ? "PRO" : "FREE";
    tierBtn.classList.toggle("is-active", isPro);

    document.querySelectorAll(".pro-locked-wrap").forEach((el) => {
      el.classList.toggle("is-locked", !isPro);
    });
  }

  function renderDeskTab(payload) {
    const spot = Number(payload.spot_price || 0);
    const md = payload.markdown_report || "";
    const retStr = extractHeaderField(md, /\*\*Returns \(24H \/ 7D \/ 30D\):\*\*\s*`([^`]+)`/);
    const rangeStr = extractHeaderField(md, /\*\*24H Range:\*\*\s*`([^`]+)`/);

    let ret24 = "";
    let ret24Pos = true;
    if (retStr) {
      ret24 = retStr.split("/")[0].trim();
      ret24Pos = !ret24.startsWith("-");
    }

    const veto = payload.section_0_veto || {};
    const vst = String(veto.veto_status || "UNDETERMINED").toUpperCase();
    const vetoClass = vst === "ACTIVE" ? "is-active" : vst === "INACTIVE" ? "is-inactive" : "is-undetermined";
    const vetoBadge = vst === "ACTIVE"
      ? `<span class="pill pill-red">VETO ACTIVE</span>`
      : vst === "INACTIVE"
      ? `<span class="pill pill-green">VETO CLEAR</span>`
      : `<span class="pill pill-amber">UNDETERMINED</span>`;
    const vetoHeadline = vst === "ACTIVE"
      ? "100% USDT Cash · New BTC Entry Prohibited"
      : vst === "INACTIVE"
      ? "Eligible for Full Multi-Gate Assessment"
      : "Fail-Closed · Verify Closed-Candle Feed";
    const vetoSub = vst === "ACTIVE"
      ? "Entry-protection lock active: lower-TF bounces or oversold RSI do not override 1D < SMA200 + 4H downtrend."
      : vst === "INACTIVE"
      ? "Both 1D SMA200 and 4H swing structure conditions are clear. Evaluate 7A/7C and 0.75% risk cap before sizing."
      : "Required closed 1D or 4H series incomplete — hold cash until verified.";

    const rsiRow = findRow(payload, "RSI(14)");
    const fgRow = findRow(payload, "Fear & Greed");
    const fundRow = findRow(payload, "Funding 8H%");
    const adxRow = findRow(payload, "ADX(14)");
    const sb = payload.stale_breakdown || { total: payload.stale_count || 0, genuine: payload.stale_count || 0, expected_headless_ws_offline: 0 };

    const kpiRsi = rsiRow ? rsiRow.value.split("·")[0].trim() : "N/A";
    const kpiFg = fgRow ? fgRow.value.split("|")[0].replace("F&G:", "").trim() : "N/A";
    const kpiFund = fundRow ? (fundRow.value.split("·")[1] || fundRow.value).trim() : "N/A";
    const kpiCov = `${payload.ok_count || 0}/${payload.total_metrics || 0} OK`;

    document.getElementById("tab-desk").innerHTML = `
      <section class="card">
        <div class="hero-price-row">
          <div>
            <div style="font-size:11px;color:var(--muted);font-weight:700;letter-spacing:0.05em;">BTC / USDT SPOT</div>
            <div class="hero-price">$${spot.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>
          </div>
          ${ret24 ? `<span class="ret-pill ${ret24Pos ? "ret-pos" : "ret-neg"}">24H ${esc(ret24)}</span>` : ""}
        </div>
        <div class="hero-meta">
          <span>24H Range: <strong style="color:var(--text)">${esc(rangeStr || "N/A")}</strong></span>
          <span>Returns: <strong style="color:var(--text)">${esc(retStr || "N/A")}</strong></span>
        </div>
      </section>

      <section class="veto-card ${vetoClass}">
        <div class="veto-top">
          <span class="veto-eyebrow">Gate 0 · Capital Preservation</span>
          ${vetoBadge}
        </div>
        <div class="veto-headline">${esc(vetoHeadline)}</div>
        <div class="veto-sub">${esc(vetoSub)}</div>
        <div class="cond-list">
          <div class="cond-row">
            <div class="cond-head">
              <span>Condition A: Closed 1D &lt; SMA 200</span>
              <span class="pill ${veto.cond_a === "YES" ? "pill-red" : veto.cond_a === "NO" ? "pill-green" : "pill-amber"}">${esc(veto.cond_a || "N/A")}</span>
            </div>
            <div class="cond-detail">${esc(veto.last_1d_close_str || "N/A")} vs ${esc(veto.sma200_1d_str || "N/A")} (${esc(veto.dist_vs_sma200_str || "N/A")})</div>
          </div>
          <div class="cond-row">
            <div class="cond-head">
              <span>Condition B: Closed 4H Structure / BOS</span>
              <span class="pill ${veto.cond_b === "YES" ? "pill-red" : veto.cond_b === "NO" ? "pill-green" : "pill-amber"}">${esc(veto.cond_b || "N/A")}</span>
            </div>
            <div class="cond-detail">${esc(veto.struct_4h_str || "N/A")} · ${esc(veto.bos_4h_str || "N/A")}</div>
          </div>
        </div>
      </section>

      <div class="kpi-grid">
        <div class="kpi-box">
          <div class="kpi-label">Momentum (RSI)</div>
          <div class="kpi-val">${esc(kpiRsi)}</div>
          <div class="kpi-sub">${esc(adxRow ? adxRow.value.split("|")[0].trim() : "Trend strength")}</div>
        </div>
        <div class="kpi-box">
          <div class="kpi-label">Sentiment (F&amp;G)</div>
          <div class="kpi-val">${esc(kpiFg)}</div>
          <div class="kpi-sub">${esc(fgRow ? (fgRow.value.split("|")[1] || "").trim() : "Market mood")}</div>
        </div>
        <div class="kpi-box">
          <div class="kpi-label">Funding 90D Rank</div>
          <div class="kpi-val">${esc(kpiFund)}</div>
          <div class="kpi-sub">${esc(fundRow ? fundRow.value.split("·")[0].trim() : "")}</div>
        </div>
        <div class="kpi-box">
          <div class="kpi-label">Feed Health</div>
          <div class="kpi-val">${esc(kpiCov)}</div>
          <div class="kpi-sub">Gen Stale: ${Number(sb.genuine || 0)} · WS_Off: ${Number(sb.expected_headless_ws_offline || 0)}</div>
        </div>
      </div>

      <div class="action-row">
        <button id="copy-ai-btn-home" class="btn btn-primary" type="button">Copy Report for Gemini</button>
        <a class="btn" href="https://github.com/aikeluargalee-tech/btc-swing-engine/actions/workflows/dd_hourly.yml" target="_blank" rel="noopener">Run Cloud Sync</a>
      </div>
    `;

    const copyHomeBtn = document.getElementById("copy-ai-btn-home");
    if (copyHomeBtn) copyHomeBtn.addEventListener("click", copyReportToClipboard);
  }

  function renderLevelsTab(payload) {
    const structList = payload.section_7a_structure || [];
    const sec7c = payload.section_7c || {};
    const ladder = sec7c.liquidation_ladder || [];
    const cal = sec7c.macro_calendar || [];
    const spot = Number(payload.spot_price || 0);
    const maxPool = Math.max(1, ...ladder.map((x) => Number(x.estimated_vol_m || 0)));

    const tfCards = structList.map((sr) => {
      const st = String(sr.structure || "");
      const cls = st.startsWith("UPTREND") ? "pill-green" : st.startsWith("DOWNTREND") ? "pill-red" : "pill-amber";
      return `
        <div class="tf-card">
          <div class="tf-top">
            <span class="tf-name">${esc(sr.tf)} <span style="color:var(--dim);font-weight:500;">(${esc(sr.bars)} bars)</span></span>
            <span class="pill ${cls}">${esc(st)}</span>
          </div>
          <div class="zone-line"><span>Resistance</span><code>${esc(sr.res)}</code></div>
          <div class="zone-line"><span>Support</span><code>${esc(sr.sup)}</code></div>
          <div class="zone-line"><span>Latest BOS</span><code>${esc(sr.bos)}</code></div>
        </div>
      `;
    }).join("");

    let upperHtml = "";
    let lowerHtml = "";
    ladder.forEach((tier) => {
      const side = String(tier.side || "").toUpperCase();
      const px = Number(tier.price || 0);
      const dp = Number(tier.distance_pct || 0);
      const vm = Number(tier.estimated_vol_m || 0);
      const widthPct = Math.min(100, Math.round((vm / maxPool) * 100));
      const rowHtml = `
        <div class="ladder-row">
          <span class="ladder-tier" style="color:${side === "UPPER" ? "var(--red)" : "var(--green)"}">${esc(tier.tier)}</span>
          <div class="ladder-bar-wrap">
            <div class="ladder-fill ${side === "UPPER" ? "upper" : "lower"}" style="width:${widthPct}%"></div>
            <span class="ladder-px">$${px.toLocaleString("en-US", { maximumFractionDigits: 0 })}</span>
            <span class="ladder-dist" style="color:${dp >= 0 ? "var(--red)" : "var(--green)"}">${dp >= 0 ? "+" : ""}${dp.toFixed(2)}%</span>
          </div>
          <span class="ladder-pool">$${vm.toFixed(0)}M</span>
        </div>
      `;
      if (side === "UPPER") upperHtml += rowHtml;
      else lowerHtml += rowHtml;
    });

    const calHtml = cal.length
      ? cal.map((c) => {
          const near = typeof c.minutes_away === "number" && c.minutes_away <= 1440;
          return `
            <div class="cal-item">
              <div>
                <div style="font-size:13px;font-weight:700;">${esc(c.title)}</div>
                <div style="font-size:11px;color:var(--muted);">${esc(c.time_utc)} · Fc: ${esc(c.forecast)} · Prev: ${esc(c.previous)}</div>
              </div>
              <span class="pill ${near ? "pill-amber" : "pill-muted"}">${esc(c.countdown)}</span>
            </div>
          `;
        }).join("")
      : `<div style="font-size:12px;color:var(--green);font-weight:700;">CLEAR — No high-impact USD events in next 7d</div>`;

    document.getElementById("tab-levels").innerHTML = `
      <div class="pro-locked-wrap ${state.tier === "free" ? "is-locked" : ""}">
        <div class="pro-lock-overlay">
          <div class="card" style="max-width:300px;text-align:center;">
            <div style="font-size:17px;font-weight:800;margin-bottom:6px;">Pro Telemetry</div>
            <div style="font-size:12px;color:var(--muted);margin-bottom:12px;">Unlock 500-Bar S/R Clusters, 6-Tier Liquidation Ladder &amp; USD Event Windows.</div>
            <button class="btn btn-primary open-paywall-btn" type="button" style="width:100%;">Start 7-Day Free Trial</button>
          </div>
        </div>
        <div class="pro-blur-target" style="display:flex;flex-direction:column;gap:12px;">
          <section class="card">
            <div class="card-title"><span>7A · 500-Bar S/R Zones</span><span class="pill pill-blue">1D / 4H / 1H</span></div>
            <div class="tf-cards">${tfCards || '<div style="font-size:12px;color:var(--muted)">No structure rows</div>'}</div>
          </section>

          <section class="card">
            <div class="card-title"><span>7C-1 · Liquidation Ladder (10x–100x)</span><span class="pill pill-muted">Modeled</span></div>
            ${upperHtml}
            <div class="spot-divider">SPOT · $${spot.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>
            ${lowerHtml}
          </section>

          <section class="card">
            <div class="card-title"><span>7C-2 · USD Macro Calendar (-60m to +7d)</span><span class="pill pill-amber">${cal.length} Events</span></div>
            ${calHtml}
          </section>
        </div>
      </div>
    `;
    bindPaywallButtons();
  }

  function renderSignalsTab(payload) {
    const panels = payload.panels || {};
    const keys = Object.keys(panels);
    const chips = [
      { id: "all", label: `All (${payload.total_metrics || 71})` },
      { id: "issues", label: "Non-OK" },
      { id: "1_price_trend_structure", label: "Price" },
      { id: "2_order_flow_liquidity", label: "Order Flow" },
      { id: "3_derivatives_options_liq", label: "Derivs" },
      { id: "4_onchain_etf_flows", label: "ETF & On-Chain" },
      { id: "5_macro_liquidity", label: "Macro" },
      { id: "6_quant_feed_health", label: "Quant" }
    ];

    const q = state.searchQuery.trim().toLowerCase();
    const listCards = [];

    keys.forEach((pk) => {
      if (state.panelFilter !== "all" && state.panelFilter !== "issues" && state.panelFilter !== pk) return;
      const p = panels[pk];
      const rows = (p.rows || []).filter((r) => {
        if (state.panelFilter === "issues" && String(r.status).toUpperCase() === "OK") return false;
        if (q) {
          const hay = (r.label + " " + r.value + " " + r.status).toLowerCase();
          if (hay.indexOf(q) === -1) return false;
        }
        return true;
      });
      if (!rows.length) return;
      listCards.push(`
        <section class="card">
          <div class="card-title"><span>${esc(p.title)}</span><span>${rows.length}</span></div>
          ${rows.map((r) => `
            <div class="metric-item">
              <div class="metric-top">
                <span class="metric-name">${esc(r.label)}</span>
                ${statusPill(r.status)}
              </div>
              <div class="metric-val">${esc(r.value)}</div>
            </div>
          `).join("")}
        </section>
      `);
    });

    const archRows = (payload.recent_archive || []).slice(0, 6).map((a) => `
      <div class="metric-item">
        <div class="metric-top">
          <span class="metric-name">${esc(a.closed_4h_bar_utc)}</span>
          <span style="font-family:var(--font-mono);font-size:12px;font-weight:700;">$${Number(a.spot_price || 0).toLocaleString("en-US", { maximumFractionDigits: 0 })}</span>
        </div>
        <div class="metric-val">OK:${a.ok_count} · N/A:${a.unavailable_count} · STALE:${a.stale_count} · PROXY:${a.proxy_or_static_count}</div>
      </div>
    `).join("");

    document.getElementById("tab-signals").innerHTML = `
      <input id="signal-search" class="search-input" type="search" placeholder="Search 71 metrics (e.g. Farside, MVRV, CVD, OI)..." value="${esc(state.searchQuery)}">
      <div class="chip-scroll">
        ${chips.map((c) => `<button class="chip ${state.panelFilter === c.id ? "is-active" : ""}" data-filter="${esc(c.id)}" type="button">${esc(c.label)}</button>`).join("")}
      </div>

      <div class="pro-locked-wrap ${state.tier === "free" ? "is-locked" : ""}">
        <div class="pro-lock-overlay">
          <div class="card" style="max-width:300px;text-align:center;">
            <div style="font-size:17px;font-weight:800;margin-bottom:6px;">71-Metric Telemetry Matrix</div>
            <div style="font-size:12px;color:var(--muted);margin-bottom:12px;">Free users see Gate 0 Veto + Core KPIs. Upgrade to Pro for full derivatives, ETF flows, and quant telemetry.</div>
            <button class="btn btn-primary open-paywall-btn" type="button" style="width:100%;">Unlock Pro Matrix</button>
          </div>
        </div>
        <div class="pro-blur-target" style="display:flex;flex-direction:column;gap:12px;">
          ${listCards.join("") || '<div class="card" style="text-align:center;color:var(--muted);font-size:12px;">No matching metrics found.</div>'}
          <section class="card">
            <div class="card-title"><span>Recent 4H SQLite Snapshots</span><span>${(payload.recent_archive || []).length} stored</span></div>
            ${archRows}
          </section>
        </div>
      </div>
    `;

    const searchInput = document.getElementById("signal-search");
    if (searchInput) {
      searchInput.addEventListener("input", (e) => {
        state.searchQuery = e.target.value;
        renderSignalsTab(payload);
        const ref = document.getElementById("signal-search");
        if (ref) {
          ref.focus();
          ref.setSelectionRange(ref.value.length, ref.value.length);
        }
      });
    }
    document.querySelectorAll(".chip[data-filter]").forEach((btn) => {
      btn.addEventListener("click", () => {
        state.panelFilter = btn.getAttribute("data-filter");
        renderSignalsTab(payload);
      });
    });
    bindPaywallButtons();
  }

  function renderProTab(payload) {
    const veto = payload.section_0_veto || {};
    const cal = (payload.section_7c && payload.section_7c.macro_calendar) || [];
    const nextEvt = cal[0];
    const isPro = state.tier === "pro";

    document.getElementById("tab-pro").innerHTML = `
      <section class="card">
        <div class="card-title"><span>Push Alerts Preview (iOS / Android)</span><span class="pill pill-blue">Simulated</span></div>
        <div class="alert-sim">
          <span class="pill pill-red">VETO</span>
          <div>
            <div style="font-size:12px;font-weight:700;">Hard Downtrend Veto: ${esc(veto.veto_status || "ACTIVE")}</div>
            <div style="font-size:11px;color:var(--muted);">Instant notification fires when closed 1D &amp; 4H conditions flip ACTIVE ↔ INACTIVE.</div>
          </div>
        </div>
        ${nextEvt ? `
          <div class="alert-sim">
            <span class="pill pill-amber">MACRO</span>
            <div>
              <div style="font-size:12px;font-weight:700;">${esc(nextEvt.title)} (${esc(nextEvt.countdown)})</div>
              <div style="font-size:11px;color:var(--muted);">Alerts 60m prior to high-impact USD macro release to pause new entries.</div>
            </div>
          </div>
        ` : ""}
      </section>

      <section class="card">
        <div class="card-title"><span>AI Desk Handoff</span><span class="pill pill-green">Ready</span></div>
        <div style="font-size:12px;color:var(--muted);line-height:1.45;margin-bottom:12px;">
          Copies the complete ${((payload.markdown_report || "").length / 1024).toFixed(1)} KB DATA-ONLY snapshot + Gate 0 rules directly for Gemini AI.
        </div>
        <div class="action-row">
          <button id="copy-ai-btn-pro" class="btn btn-primary" type="button">Copy Full Markdown</button>
          <a class="btn" href="../index.html">Open Web Matrix</a>
        </div>
      </section>

      <section class="card">
        <div class="card-title"><span>Monetization Preview</span><span class="pill ${isPro ? "pill-green" : "pill-amber"}">${isPro ? "PRO ACTIVE" : "FREE TIER"}</span></div>
        <div style="font-size:12px;color:var(--muted);line-height:1.45;margin-bottom:12px;">
          Toggle <strong>PRO / FREE</strong> in the top-right header to test locked Pro cards, or open the native RevenueCat subscription sheet below.
        </div>
        <button class="btn btn-primary open-paywall-btn" type="button" style="width:100%;">Preview Pro Paywall Sheet</button>
      </section>

      <div class="disclaimer">
        Market intelligence &amp; risk telemetry only. Non-custodial, no trade execution, not financial advice.
      </div>
    `;

    const copyPro = document.getElementById("copy-ai-btn-pro");
    if (copyPro) copyPro.addEventListener("click", copyReportToClipboard);
    bindPaywallButtons();
  }

  function renderAll() {
    if (!state.payload) return;
    renderHeader(state.payload);
    renderDeskTab(state.payload);
    renderLevelsTab(state.payload);
    renderSignalsTab(state.payload);
    renderProTab(state.payload);
  }

  async function copyReportToClipboard() {
    const md = state.payload && state.payload.markdown_report;
    if (!md) return;
    try {
      await navigator.clipboard.writeText(md);
      showToast("Copied full DD report for Gemini AI");
    } catch (_) {
      const ta = document.createElement("textarea");
      ta.value = md;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand("copy");
      ta.remove();
      showToast("Copied full DD report for Gemini AI");
    }
  }

  function bindPaywallButtons() {
    const modal = document.getElementById("paywall-modal");
    document.querySelectorAll(".open-paywall-btn").forEach((btn) => {
      btn.addEventListener("click", () => modal.classList.add("is-open"));
    });
  }

  async function loadSnapshot(manual) {
    const refreshBtn = document.getElementById("refresh-btn");
    if (refreshBtn) refreshBtn.classList.add("spinning");
    try {
      const res = await fetch("../dd_latest.json?t=" + Date.now(), { cache: "no-store" });
      if (!res.ok) throw new Error("HTTP " + res.status);
      state.payload = await res.json();
      renderAll();
      if (manual) showToast("Telemetry refreshed");
    } catch (err) {
      showToast("Sync error: " + err.message);
    } finally {
      if (refreshBtn) refreshBtn.classList.remove("spinning");
    }
  }

  function init() {
    try { localStorage.removeItem("cortex_pwa_look"); } catch (_) {}

    document.querySelectorAll(".nav-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        const target = btn.getAttribute("data-tab");
        state.activeTab = target;
        document.querySelectorAll(".nav-btn").forEach((b) => b.classList.toggle("is-active", b === btn));
        document.querySelectorAll(".tab-view").forEach((v) => v.classList.toggle("is-active", v.id === "tab-" + target));
        window.scrollTo({ top: 0, behavior: "smooth" });
      });
    });

    document.getElementById("tier-toggle-btn").addEventListener("click", () => {
      state.tier = state.tier === "pro" ? "free" : "pro";
      renderAll();
      showToast(state.tier === "pro" ? "Switched to PRO preview" : "Switched to FREE preview (locked)");
    });

    document.getElementById("refresh-btn").addEventListener("click", () => loadSnapshot(true));

    const modal = document.getElementById("paywall-modal");
    document.getElementById("close-paywall-btn").addEventListener("click", () => modal.classList.remove("is-open"));
    modal.addEventListener("click", (e) => {
      if (e.target === modal) modal.classList.remove("is-open");
    });

    document.querySelectorAll(".plan-box").forEach((box) => {
      box.addEventListener("click", () => {
        state.selectedPlan = box.getAttribute("data-plan");
        document.querySelectorAll(".plan-box").forEach((b) => b.classList.toggle("is-selected", b === box));
      });
    });

    document.getElementById("demo-subscribe-btn").addEventListener("click", () => {
      state.tier = "pro";
      modal.classList.remove("is-open");
      renderAll();
      showToast("Pro unlocked (demo preview)");
    });

    if ("serviceWorker" in navigator) {
      navigator.serviceWorker.register("./sw.js").catch(() => {});
    }

    loadSnapshot(false);
    setInterval(() => {
      if (state.payload) renderHeader(state.payload);
    }, 30000);
  }

  document.addEventListener("DOMContentLoaded", init);
})();
