/**
 * BTC Swing Mobile PWA Client Controller
 * Battery-conscious, responsive, touch-optimized frontend controller.
 */

// Global State
let currentMetrics = null;
let activeScreen = 1; // 1: Cockpit, 2: Deep Dive, 3: Field Manual
let ws = null;
let pollInterval = null;
let currentTheme = 'titanium';

// DOM Elements cache
const el = {
  spotPrice: document.getElementById('val-spot-price'),
  spotChange: document.getElementById('val-spot-change'),
  sessionBadge: document.getElementById('val-session-badge'),
  connDot: document.getElementById('conn-dot'),
  connText: document.getElementById('conn-text'),
  
  // Hero Gauge
  gaugeArc: document.getElementById('gauge-arc'),
  gaugeScore: document.getElementById('gauge-score'),
  regimePill: document.getElementById('regime-pill'),
  regimeText: document.getElementById('regime-text'),

  // Trade Plan Card
  tradePlanContainer: document.getElementById('trade-plan-card-container'),

  // 4 Pillars
  p1Bar: document.getElementById('p1-bar'),
  p1Score: document.getElementById('p1-score'),
  p1Status: document.getElementById('p1-status'),
  p1Summary: document.getElementById('p1-summary'),

  p2Bar: document.getElementById('p2-bar'),
  p2Score: document.getElementById('p2-score'),
  p2Status: document.getElementById('p2-status'),
  p2Summary: document.getElementById('p2-summary'),

  p3Bar: document.getElementById('p3-bar'),
  p3Score: document.getElementById('p3-score'),
  p3Status: document.getElementById('p3-status'),
  p3Summary: document.getElementById('p3-summary'),

  p4Bar: document.getElementById('p4-bar'),
  p4Score: document.getElementById('p4-score'),
  p4Status: document.getElementById('p4-status'),
  p4Summary: document.getElementById('p4-summary'),

  // Deep Dive
  ddCval: document.getElementById('dd-cval'),
  ddCpoc: document.getElementById('dd-cpoc'),
  ddCvah: document.getElementById('dd-cvah'),
  ddPatName: document.getElementById('dd-pat-name'),
  ddPatBias: document.getElementById('dd-pat-bias'),
  ddPatConf: document.getElementById('dd-pat-conf'),
  ddPatNeck: document.getElementById('dd-pat-neck'),
  ddLiqPool: document.getElementById('dd-liq-pool'),
  ddLiqDist: document.getElementById('dd-liq-dist'),
  ddLiqRrr: document.getElementById('dd-liq-rrr'),

  // Toast
  toast: document.getElementById('mobile-toast'),
  toastMsg: document.getElementById('toast-msg'),
};

/**
 * Initializes WebSocket connection with fallback to REST polling.
 */
function initDataFeed() {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = `${protocol}//${window.location.host}/ws/metrics`;

  try {
    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      setConnectionStatus(true, '1 Hz LIVE');
      if (pollInterval) {
        clearInterval(pollInterval);
        pollInterval = null;
      }
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        updateUI(data);
      } catch (err) {
        console.error('Error parsing WebSocket message:', err);
      }
    };

    ws.onerror = () => {
      fallbackToRestPolling();
    };

    ws.onclose = () => {
      setConnectionStatus(false, 'RECONNECTING');
      fallbackToRestPolling();
      setTimeout(initDataFeed, 3000);
    };
  } catch (e) {
    fallbackToRestPolling();
  }
}

function fallbackToRestPolling() {
  if (pollInterval) return;
  setConnectionStatus(false, 'REST POLL');
  fetchMetrics();
  pollInterval = setInterval(fetchMetrics, 1500);
}

async function fetchMetrics() {
  try {
    const res = await fetch('/api/v1/metrics/latest');
    if (res.ok) {
      const data = await res.json();
      updateUI(data);
      setConnectionStatus(true, 'REST ACTIVE');
    }
  } catch (err) {
    setConnectionStatus(false, 'OFFLINE');
  }
}

function setConnectionStatus(connected, text) {
  if (el.connDot && el.connText) {
    el.connDot.className = connected
      ? 'w-2 h-2 rounded-full bg-emerald-400 animate-pulse'
      : 'w-2 h-2 rounded-full bg-rose-500';
    el.connText.textContent = text;
  }
}

/**
 * Updates all UI elements from incoming data payload.
 */
function updateUI(data) {
  currentMetrics = data;

  // Header
  if (el.spotPrice) {
    el.spotPrice.textContent = `$${data.spot_price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  }
  if (el.spotChange) {
    el.spotChange.textContent = `+${data.spot_change_24h_pct}%`;
  }
  if (el.sessionBadge) {
    el.sessionBadge.textContent = data.market_session || 'GLOBAL MARKET';
  }

  // Hero Gauge (Arc length ~251.2 for r=40 semi-circle or stroke-dashoffset)
  const score = data.confluence_score || 0;
  if (el.gaugeScore) {
    el.gaugeScore.textContent = `${Math.round(score)}`;
  }

  // Animate SVG gauge needle / stroke (gauge arc has length 251.2)
  if (el.gaugeArc) {
    const maxDash = 251.2;
    const offset = maxDash - (maxDash * (score / 100.0));
    el.gaugeArc.style.strokeDashoffset = Math.max(0, offset);

    // Color gradient based on score
    if (score >= 80) {
      el.gaugeArc.style.stroke = '#34d399'; // Emerald
    } else if (score >= 70) {
      el.gaugeArc.style.stroke = '#38bdf8'; // Cyan
    } else if (score >= 50) {
      el.gaugeArc.style.stroke = '#fbbf24'; // Amber
    } else {
      el.gaugeArc.style.stroke = '#f87171'; // Rose
    }
  }

  // Regime Pill
  if (el.regimePill && el.regimeText) {
    el.regimeText.textContent = `${data.confluence_label} • ${data.regime.replace(/_/g, ' ')}`;
    el.regimePill.className = `inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-mono font-bold border transition ${getRegimeBadgeClass(data.regime_color)}`;
  }

  // Trade Plan Card
  renderTradePlanCard(data.trade_plan);

  // 4 Pillars
  const p = data.pillars || {};
  renderPillar(el.p1Bar, el.p1Score, el.p1Status, el.p1Summary, p.order_flow);
  renderPillar(el.p2Bar, el.p2Score, el.p2Status, el.p2Summary, p.derivatives);
  renderPillar(el.p3Bar, el.p3Score, el.p3Status, el.p3Summary, p.macro);
  renderPillar(el.p4Bar, el.p4Score, el.p4Status, el.p4Summary, p.volatility);

  // Deep Dive
  const dd = data.deep_dive || {};
  if (el.ddCval && dd.auction) {
    el.ddCval.textContent = `$${dd.auction.cval.toLocaleString()}`;
    el.ddCpoc.textContent = `$${dd.auction.cpoc.toLocaleString()}`;
    el.ddCvah.textContent = `$${dd.auction.cvah.toLocaleString()}`;
  }
  if (el.ddPatName && dd.classic_pattern) {
    el.ddPatName.textContent = dd.classic_pattern.name;
    el.ddPatBias.textContent = dd.classic_pattern.bias;
    el.ddPatConf.textContent = `${dd.classic_pattern.confidence_pct}% Match`;
    el.ddPatNeck.textContent = `$${dd.classic_pattern.neckline.toLocaleString()}`;
  }
  if (el.ddLiqPool && dd.liquidation_magnet) {
    el.ddLiqPool.textContent = `$${dd.liquidation_magnet.overhead_short_pool.toLocaleString()}`;
    el.ddLiqDist.textContent = `+${dd.liquidation_magnet.distance_pct}% Above`;
    el.ddLiqRrr.textContent = `1:${dd.liquidation_magnet.rrr_estimate}`;
  }
}

function getRegimeBadgeClass(color) {
  switch (color) {
    case 'emerald':
      return 'bg-emerald-950/80 border-emerald-500/60 text-emerald-300';
    case 'sky':
      return 'bg-sky-950/80 border-sky-500/60 text-sky-300';
    case 'amber':
      return 'bg-amber-950/80 border-amber-500/60 text-amber-300';
    case 'rose':
    default:
      return 'bg-rose-950/80 border-rose-500/60 text-rose-300';
  }
}

function renderPillar(barEl, scoreEl, statusEl, summaryEl, pillarData) {
  if (!pillarData) return;
  if (barEl) barEl.style.width = `${pillarData.pct}%`;
  if (scoreEl) scoreEl.textContent = `${pillarData.score}/${pillarData.max}`;
  if (statusEl) statusEl.textContent = pillarData.status;
  if (summaryEl) summaryEl.textContent = pillarData.summary;
}

function renderTradePlanCard(plan) {
  if (!el.tradePlanContainer || !plan) return;

  if (plan.is_active) {
    // ACTIVE TRADE PLAN CARD (Confluence >= 70)
    el.tradePlanContainer.innerHTML = `
      <div class="rounded-2xl bg-gradient-to-b from-slate-900 to-slate-950 border border-emerald-500/40 p-4 shadow-xl space-y-3 relative overflow-hidden">
        <div class="absolute -right-8 -top-8 w-28 h-28 bg-emerald-500/10 rounded-full blur-2xl pointer-events-none"></div>
        
        <div class="flex items-center justify-between border-b border-slate-800 pb-2">
          <div class="flex items-center gap-2">
            <span class="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse"></span>
            <span class="text-xs font-mono font-bold tracking-wider text-emerald-300 uppercase">DETERMINISTIC SPOT PLAN</span>
          </div>
          <span class="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-emerald-950 border border-emerald-600/60 text-emerald-300">
            ARMED &bull; 0.75% RISK CAP
          </span>
        </div>

        <div class="grid grid-cols-2 gap-2 text-xs font-mono">
          <div class="bg-black/40 p-2.5 rounded-xl border border-slate-800/80">
            <div class="text-slate-400 text-[10px] uppercase">ENTRY RANGE</div>
            <div class="text-white font-black text-sm mt-0.5">${plan.entry_zone}</div>
            <div class="text-[9px] text-emerald-400 font-semibold mt-0.5">Limit Bid Zone</div>
          </div>
          <div class="bg-black/40 p-2.5 rounded-xl border border-slate-800/80">
            <div class="text-slate-400 text-[10px] uppercase">HARD INVALIDATION</div>
            <div class="text-rose-400 font-black text-sm mt-0.5">$${plan.invalidation_floor.toLocaleString()}</div>
            <div class="text-[9px] text-slate-500 mt-0.5">${plan.invalidation_distance_pct}% Floor Stop</div>
          </div>
          <div class="bg-black/40 p-2.5 rounded-xl border border-slate-800/80">
            <div class="text-slate-400 text-[10px] uppercase">TAKE PROFIT 1 (${plan.take_profit_1_rrr})</div>
            <div class="text-cyan-300 font-black text-sm mt-0.5">$${plan.take_profit_1.toLocaleString()}</div>
            <div class="text-[9px] text-slate-500 mt-0.5">Scale Out 50%</div>
          </div>
          <div class="bg-black/40 p-2.5 rounded-xl border border-slate-800/80">
            <div class="text-slate-400 text-[10px] uppercase">TAKE PROFIT 2 (${plan.take_profit_2_rrr})</div>
            <div class="text-emerald-300 font-black text-sm mt-0.5">$${plan.take_profit_2.toLocaleString()}</div>
            <div class="text-[9px] text-slate-500 mt-0.5">Short Liq Pool Target</div>
          </div>
        </div>

        <!-- Position Sizing Formula Box -->
        <div class="rounded-xl bg-emerald-950/30 border border-emerald-800/40 p-2.5 flex items-center justify-between text-xs font-mono">
          <div>
            <div class="text-[10px] text-slate-400">POSITION SIZING (0.75% RISK)</div>
            <div class="text-white font-bold mt-0.5">
              <span class="text-emerald-400 text-sm font-black">${plan.position_size_btc} BTC</span>
              <span class="text-slate-400 text-xs">($${plan.notional_usd.toLocaleString()})</span>
            </div>
          </div>
          <div class="text-right">
            <div class="text-[10px] text-slate-400">MAX LOSS AT STOP</div>
            <div class="text-rose-400 font-black text-sm">-$${plan.max_risk_usd.toFixed(2)}</div>
          </div>
        </div>
      </div>
    `;
  } else {
    // DEFENSIVE STANDBY CARD (Confluence < 70)
    el.tradePlanContainer.innerHTML = `
      <div class="rounded-2xl bg-slate-900/90 border border-amber-500/40 p-4 shadow-xl space-y-2.5">
        <div class="flex items-center justify-between border-b border-slate-800 pb-2">
          <div class="flex items-center gap-2">
            <span class="w-2.5 h-2.5 rounded-full bg-amber-400"></span>
            <span class="text-xs font-mono font-bold tracking-wider text-amber-300 uppercase">DEFENSIVE STANCE</span>
          </div>
          <span class="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-amber-950 border border-amber-600/50 text-amber-300">
            100% CASH DEFENSE
          </span>
        </div>
        <div class="text-xs text-slate-300 leading-relaxed font-sans">
          ${plan.missing_gate_reason || 'Confluence is below 70.0 threshold. Zero risk taken in unconfirmed regimes.'}
        </div>
        <div class="text-[10px] text-slate-400 font-mono bg-black/40 rounded-lg p-2 border border-slate-800 flex items-center justify-between">
          <span>Active Allocation: <strong class="text-white">100% Cash / USDT</strong></span>
          <span class="text-emerald-400 font-bold">$0 Capital at Risk</span>
        </div>
      </div>
    `;
  }
}

/**
 * Screen Navigation (1: Cockpit, 2: Deep Dive, 3: Field Manual)
 */
function setScreen(screenNum) {
  activeScreen = screenNum;
  [1, 2, 3].forEach(num => {
    const scr = document.getElementById(`screen-${num}`);
    const tabBtn = document.getElementById(`nav-btn-${num}`);
    if (scr) {
      if (num === screenNum) {
        scr.classList.remove('hidden');
      } else {
        scr.classList.add('hidden');
      }
    }
    if (tabBtn) {
      if (num === screenNum) {
        tabBtn.className = "flex-1 py-2 rounded-xl bg-cyan-500 text-slate-950 font-bold text-xs font-mono transition shadow-md shadow-cyan-500/20";
      } else {
        tabBtn.className = "flex-1 py-2 rounded-xl bg-slate-900/60 text-slate-400 hover:text-white font-medium text-xs font-mono transition";
      }
    }
  });
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

/**
 * Accordion Toggle Helper
 */
function toggleAccordion(id) {
  const content = document.getElementById(`acc-content-${id}`);
  const icon = document.getElementById(`acc-icon-${id}`);
  if (content) {
    if (content.classList.contains('hidden')) {
      content.classList.remove('hidden');
      if (icon) icon.textContent = '▲';
    } else {
      content.classList.add('hidden');
      if (icon) icon.textContent = '▼';
    }
  }
}

/**
 * 1-Tap Copy AI Audit Packet
 */
async function copyAIAuditPacket() {
  let textToCopy = '';
  if (currentMetrics && currentMetrics.ai_audit_snippet) {
    textToCopy = currentMetrics.ai_audit_snippet;
  } else {
    try {
      const res = await fetch('/api/v1/ai-packet');
      textToCopy = await res.text();
    } catch {
      textToCopy = '# BTC Swing Engine Live Telemetry Snapshot';
    }
  }

  if (navigator.clipboard) {
    try {
      await navigator.clipboard.writeText(textToCopy);
      showToast('📋 Ready-to-Paste AI Packet Copied for Grok / Claude!');
      return;
    } catch (e) {
      console.warn('Clipboard write failed, using fallback');
    }
  }

  // Fallback for older browsers
  const textarea = document.createElement('textarea');
  textarea.value = textToCopy;
  document.body.appendChild(textarea);
  textarea.select();
  document.execCommand('copy');
  document.body.removeChild(textarea);
  showToast('📋 Ready-to-Paste AI Packet Copied!');
}

function copyPromptTemplate(templateKey) {
  let promptText = '';
  if (templateKey === 'grok') {
    promptText = `You are the Chief Quantitative Risk Officer. Audit this live BTC Swing Engine telemetry packet against the 4-Pillar Confluence and 1:3 RRR Liquidation Magnet Law. Identify any subtle tape frictions or divergences and output an independent verdict (Green/Yellow/Red):

${currentMetrics ? currentMetrics.ai_audit_snippet : ''}`;
  } else if (templateKey === 'claude') {
    promptText = `Conduct a rigorous second-opinion risk audit of this BTC Spot Swing Plan. Review the 0.75% equity risk sizing and confirm if the Invalidation Stop provides adequate buffer below the 4H sweep wick:

${currentMetrics ? currentMetrics.ai_audit_snippet : ''}`;
  }
  navigator.clipboard.writeText(promptText);
  showToast(`📋 ${templateKey.toUpperCase()} Audit Prompt Copied!`);
}

function showToast(msg) {
  if (el.toast && el.toastMsg) {
    el.toastMsg.textContent = msg;
    el.toast.classList.remove('opacity-0', 'pointer-events-none', 'translate-y-4');
    el.toast.classList.add('opacity-100', 'translate-y-0');
    setTimeout(() => {
      el.toast.classList.remove('opacity-100', 'translate-y-0');
      el.toast.classList.add('opacity-0', 'pointer-events-none', 'translate-y-4');
    }, 2800);
  }
}

/**
 * Theme Switcher (Modern Titanium vs Retro IBM vs Tactical HUD)
 */
function setTheme(theme) {
  currentTheme = theme;
  const root = document.getElementById('mobile-app-root');
  if (!root) return;

  root.classList.remove('theme-ibm', 'theme-tactical');
  if (theme === 'ibm') {
    root.classList.add('theme-ibm');
    showToast('📟 Retro IBM 3270 Theme Activated');
  } else if (theme === 'tactical') {
    root.classList.add('theme-tactical');
    showToast('✈️ Tactical Aerospace HUD Theme Activated');
  } else {
    showToast('💎 Modern Titanium FinTech Theme Activated');
  }
}

// Service worker registration
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js').catch(() => {});
  });
}

// Start feed on DOM ready
document.addEventListener('DOMContentLoaded', () => {
  initDataFeed();
});
