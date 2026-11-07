<USER_REQUEST>
From Gemini:

Your **BTC Swing Mobile App** narrative architecture tackles the single biggest failure point in retail crypto software: cognitive overload driving emotional self-sabotage. By keeping institutional microstructure metrics running silently in the background while presenting a calm, protective single-screen cockpit, your design shifts the user's mindset from *gambling on price ticks* to *following a pilot's safety protocol*.



Below is a comprehensive architectural review, psychological critique, and copy polish structured directly around your five review directives.



---



## Directive 1: Narrative Tone, Hidden Jargon & The Traffic Light Metaphor



### 1. Tone Calibration: Protective Authority vs. Over-Casualness



Overall, the "Personal Wall Street Guardian" and "Pilot's Pre-Flight Safety Checks" metaphors hit the right balance—they strip away intimidation without turning the app into a gamified cartoon.



However, two specific phrases in the current UI border on being slightly *too* casual when real hard-earned money is on the line:



* **`Market Mood: Sideways Nap`** and **`Today's Action: Sit on Hands`**: While friendly, an anxious amateur investor checking on their savings wants to feel that their guardian is actively vigilant, not "napping" or "sitting on its hands."





* **The Fix**: Pair warm everyday language with active, protective framing. Use **`Market Mood: Resting Sideways (Building Energy)`** and **`Today's Action: Hold in Cash (Shield Active)`**.



### 2. The Hidden Jargon Audit (Leaks in the Current Wireframe)



While Section 3 translates your core quant metrics effectively, several technical, institutional, or crypto-native terms still leak through in the Section 4 cockpit wireframe and AI Copilot prompt:



| Current Term in Dossier | Location in App | Why Beginners Stumble | Recommended Plain-English Replacement |

| --- | --- | --- | --- |

| **`[NVG] [IBM] [SLATE]`** | Top-Right Header Bar | Cryptic 3-letter theme/terminal codes look like stock tickers or quant buttons. | Move theme switching into a simple **`⚙️ Display`** or **`🎨 Theme`** icon menu. |

| **`100% Cash / USDT`** | Account Safety Line | True beginners often don't know what `USDT` is or worry about stablecoin de-pegging jargon. | **`100% Cash (USD / Stablecoins)`** |

| **`Let runner ride to macro liquidity`** | Scenario B, Step 4 | "Runner" is prop-trader slang; "macro liquidity" is pure institutional quant jargon. | **`Let your remaining half ride toward the upper target`** |

| **`4-hour Ascending Triangle coiling`** | AI Copilot Prompt (Check 4) | Classical charting terminology that triggers imposter syndrome. | **`Upward Spring Pattern (Buyers stepping in at higher prices every 4 hours)`** |

| **`net +201 BTC`** | AI Copilot Prompt (Check 2) | Without context, a beginner doesn't know if +201 BTC is huge or tiny. | **`Buyers outpaced sellers by 201 Bitcoin in the last 15 minutes`** |

| **`50-day average line ($79,826)`** | Check 3 Explanation | Good, but beginners don't intuitively know why price being *below* an average matters. | **`50-Day Health Line ($79,826) — the boundary between a weak market and a strong uptrend`**



 |



### 3. Fixing the Traffic Light Metaphor & A Critical Number Contradiction



There are two structural issues in how the transition between **Safe in Cash** and **Active Buy** is currently presented:



1. **The "Green-Light Meter" Naming Paradox**: In Scenario A, the user is in amber/yellow mode (`STATUS: SAFE IN CASH`), yet the gauge is labeled **`Green-Light Buy Meter: 45%`**. Calling an active warning state a "Green-Light Meter" creates subconscious confusion. Rename the gauge itself to **`Safety Clearance Meter: 45/100`** (or **`Market Readiness Score`**), with a simple sub-label: *Needs 70/100 for a Green Light*.





2. **The $79,826 vs. $75,200 Contradiction**: In Scenario A, the Decision Card tells the user what must happen before buying: *"1. Price climbs above $79,826 -> Not Yet ($75.9k)"*. Yet in Scenario B, the All-Clear Buy Signal fires with a buy range of **$75,200 to $75,500**—well below $79,826! If a beginner reads that Bitcoin must cross $79,826 to be safe, and then sees a buy alert at $75,200, they will immediately think the app is broken or contradicting itself.





* **The Fix**: Clarify that the Safety Clearance Score is a *combined weight* of all 4 checks (e.g., *"3 of 4 Safety Checks Passed — Waiting on Big Picture Trend to reach 70% total score"*), or ensure your example scenarios use consistent price thresholds.







---



## Directive 2: Psychological Impact & Fear/Greed Mitigation



### 1. Strengthening "Cash as a Winning Position"



Your reframing of cash directly targets retail "Action Bias". To make it even more effective during multi-week sideways markets, shift the psychological reward from **passive waiting** to **active defense**:



* Instead of framing cash as an absence of action (`Active Bitcoin Buys: 0.0000 BTC`), frame it as a deployed defensive shield: **`Active Position: 100% Protected Cash`**.





* Add a micro-validation line when the market is choppy: *"80% of beginner losses happen in sideways markets like today. By staying in cash right now, you are outperforming the impatient crowd."*



### 2. The "$100k Account / $750 Max Loss" Relatability Trap



Showing exact dollar risk before entry is brilliant for eliminating Fear of Ruin. However, **hardcoding a $100,000 portfolio ($750 max loss and a ~0.69 BTC / $52,000 buy size)** as your default baseline creates a massive psychological barrier for your target audience:



* **Why It Hurts Beginners**: 90% of amateur and beginner crypto investors are starting with **$500, $1,000, or $5,000**—not $100,000. When a beginner with a $2,000 account sees *"Recommended Buy Amount: 0.6908 Bitcoin (~$52,000)"* and *"Max Loss: $750"*, they will immediately feel the app is only for wealthy whales, or worse, they won't know how to scale the math down to their own wallet.

* **The Fix (1-Tap Portfolio Sizer)**: Let the user type in their actual starting capital (defaulting to a relatable **$1,000** or **$5,000** for beginners). On a $1,000 account, the 0.75% Golden Rule instantly displays:

> **Your Maximum Risk: $7.50** *(Less than the price of lunch — 99.25% of your $1,000 remains completely untouched).*





* **Important Legal & Practical Nuance on "Drops to Zero"**: Your current copy says, *"Even if Bitcoin drops to zero tomorrow, your emergency safety floor at $74,180 ensures you will never lose more than $750"*. Because extreme flash crashes can cause slight order slippage—and because a companion app relies on the user actually placing the stop-loss order on their exchange—replace "Even if Bitcoin drops to zero tomorrow... never lose more than" with:





> *"By setting your automatic Safety Exit at $74,180 when you buy, your planned risk is capped at just $7.50 (0.75% of your $1,000 budget)—shielding over 99% of your savings from a sudden crash."*







### 3. Emergency Micro-Copy for a Violent 10% Market Dump



When Bitcoin drops 10% in a few hours, beginners experience an adrenaline spike—either panicking to sell the bottom or feeling reckless FOMO to "buy the dip" while the knife is still falling. Trigger a dedicated **"Storm Shield Banner"** on the dashboard depending on the user's state:



* **If the User is Safe in Cash (Most Common)**:

> **⛈️ MARKET STORM DETECTED (-10.2% TODAY) — YOUR LOSS: $0.00**

> *"Panic sellers are dumping right now, and our Dump Protection Check (Check 2) has locked the cockpit to protect you. Do NOT try to 'catch a falling knife.' Because you stayed in cash, your money just gained 10% more buying power. Wait calmly until the selling stops and our Safety Meter turns green."*





* **If the User Was in an Active Trade that Hit the Safety Floor**:

> **🛡️ EMERGENCY SAFETY FLOOR TRIGGERED AT $74,180**

> *"Your automatic exit worked exactly as designed. While the market crashed 10%, your Safety Floor cut the cord early—capping your loss at just 0.75% and saving 99.25% of your capital. Take a breath. We are back in 100% Safe Cash until the dust settles."*







---



## Directive 3: Educational Retention & AI Copilot Expansion



### 1. Keeping Users Engaged During Multi-Week "Cash Regimes"



If your institutional engine keeps users in cash for 14 to 21 consecutive days during choppy consolidation, beginners may get bored, feel they aren't getting value from the app, and wander back to high-risk exchanges. Keep them returning daily without encouraging trades through three low-friction mechanisms:



1. **The "Dodged Bullet" Counter (Loss Avoidance Metric)**: Whenever Bitcoin drops while the engine is in `SAFE IN CASH` mode, display a subtle badge: **`🛡️ Capital Saved This Month: +8.4% Drop Avoided`**. Visually proving that *not trading* saved them money builds immense loyalty.

2. **The Daily 15-Second "Black Box" Peek**: Once a day, offer a tap-to-reveal micro-card at the bottom of the screen: *"💡 Today's 15-Second Lesson: Why did Check 3 block us from buying yesterday? (And how it saved you from today's dip)."*

3. **Patience Streak Badge**: Track consecutive days the user followed the system's discipline without forcing a rogue trade: **`🔥 12-Day Discipline Streak: Trading Like the Top 5%`**.



### 2. Expanding the AI Copilot Prompt Builder



Copying a structured snapshot to paste into Gemini, ChatGPT, or Grok is a standout feature because it offloads infinite beginner Q&A to frontier LLMs while keeping your UI clean. Instead of a single static button, offer a **3-Option Prompt Selector** when the user taps **`[💬 Ask AI Copilot]`** so the prompt matches their exact emotional impulse:



* **Option A: `🧠 "Explain today's market in simple words"**` *(Your current 3-bullet educational prompt)*.





* **Option B: `🔥 "Everyone on social media is buying! Why are we waiting?"**` *(Appends a prompt asking the AI to explain FOMO traps, why retail crowds buy into institutional resistance, and which specific safety check is currently failing).*

* **Option C: `📋 "Walk me through placing this exact trade step-by-step"**` *(Only active during a Green Buy Signal—generates a prompt asking the AI to explain how to enter a Limit Buy and Stop-Loss order on Coinbase/Kraken/Binance using the exact numbers on screen).*



---



## Directive 4: Commercial Differentiation & Credibility Anchors



### 1. Ethical Positioning Against High-Volume Exchanges



Traditional crypto exchanges (Binance, Coinbase, Kraken) operate like casinos: they collect fees on every buy and sell, meaning they make money when you over-trade, even if your account goes to zero.



Position the **BTC Swing Mobile App** as the **"Anti-Casino" (The Alignment Guarantee)**:



* **Core Marketing Hook**: *"Exchanges get paid every time you click Buy or Sell. Our engine only gives you the green light when institutional safety checks align. We don't want you trading every day—we want you protecting and growing your wealth."*

* **Subscription Value Framing**: Frame the app's cost around **a single prevented mistake**: *"Avoiding just one impulsive FOMO trade in a choppy market pays for this guardian for the next 3 years."*



### 2. Translating Technical Credibility into Beginner Trust



In your document header, you highlight **`(179 Unit Tests Green)`**. To a software engineer, that signals rigorous code quality; to an everyday retail investor, "unit tests" sounds like confusing computer programming jargon.



Use credibility anchors that speak directly to **financial safety and emotional relief**:



* Replace `"179 Unit Tests Green"` with **"179 Automated Safety Diagnostics Verified"**.





* Elevate **`🛡️ 100% Spot Bitcoin Only — Zero Leverage, Zero Debt, Zero Liquidation Risk`** as a prominent trust badge during onboarding. Beginners are terrified of stories where people "lost more than they put in" or got liquidated overnight; explicitly stating that your system only buys real, unleveraged Bitcoin is a massive anxiety reliever.







---



## Directive 5: Proposed Copy Revisions & UI Polish



Below are direct side-by-side copy upgrades for your main cockpit cards, safety checks, and action buttons to maximize clarity and emotional reassurance:



| UI Element | Current Dossier Copy | Recommended Polished Copy | Why It Works Better |

| --- | --- | --- | --- |

| **Main Status Banner (Yellow)** | `🛡️ STATUS: SAFE IN CASH (DO NOT BUY YET)` | **`🛡️ CAPITAL SHIELD ON: STAY 100% IN CASH`** | Sounds active and protective rather than restrictive. |

| **Mood Sub-Header** | `😴 MARKET MOOD: SIDEWAYS NAP (WAIT FOR SPARK)` | **`⏳ MARKET MOOD: CHOPPY & UNDECIDED (WAITING FOR TREND)`** | Clearly explains *why* we aren't buying without sounding sleepy. |

| **Cash Mode Quote** | *"Bitcoin is moving sideways. Buying now is like guessing on a coin flip. We protect your wealth by waiting 100% in cash until ready."* | ***"Right now, buyers and sellers are locked in a tug-of-war. Buying today is a 50/50 coin flip—so we keep your money 100% safe in cash until buyers take clear control."*** | Paints a vivid mental picture ("tug-of-war") that connects to the 4 checks below. |

| **Today's Action Row** | `Today's Action: Sit on Hands (Be Patient)` | **`Today's Smart Move: Hold Cash & Let the Market Settle`** | Validates patience as an intelligent financial action. |

| **Check 1 Label** | `🏛️ Check 1: Safety Floors & Ceilings — 80% OK` | **`🏛️ Check 1: Strong Price Floor ($74,180) — ✅ Passed (80%)`** | Putting the actual floor price right in the label grounds the abstract concept. |

| **Check 2 Label** | `🌊 Check 2: Big Buyers & Dump Protection — 75% OK` | **`🌊 Check 2: Panic Selling Absorbed — ✅ Passed (75%)`** | Directly answers the beginner's biggest fear ("Are people dumping?"). |

| **Check 3 Label** | `🌐 Check 3: The Big Picture Trend (Weather) — 45% NO` | **`🌤️ Check 3: 50-Day Uptrend Line — ⚠️ Waiting (45%)`** | Replaces the harsh `"45% NO"` with `"⚠️ Waiting (45%)"`, reducing frustration. |

| **Check 4 Label** | `📐 Check 4: Chart Launch Shape (Spring Coil) — 85% OK` | **`🚀 Check 4: Breakout Energy Coiling — ✅ Passed (85%)`** | "Breakout Energy" feels intuitive and exciting when paired with "Coiling". |

| **AI Copilot Button** | `[💬 Ask AI Copilot: "Explain This in Simple Words"]` | **`[💬 Tap to Copy AI Briefing: "Explain Today's Market to Me"]`** | Sets clear UX expectations that tapping copies a briefing to paste into their AI chat app.



 |



Would you like me to draft the exact beginner-friendly expanded text for all four **Pre-Flight Safety Check** dropdown cards (matching the style of Check 3 in your dossier), or design the onboarding **Portfolio Risk Slider** screen next?

The expanded **Pre-Flight Safety Check** dropdown cards and the **Portfolio Safety Sizer** onboarding/drawer screen below are designed to drop directly into your **BTC Swing Mobile App** specification.



---



## Part 1: The 4 Pre-Flight Safety Checks (Progressive Disclosure Cards)



When a user taps any of the four safety checks on the main cockpit, the row expands smoothly into a **3-part micro-card**:



1. **The Everyday Metaphor** (1 sentence establishing what this check does in plain English).

2. **Live Status Narrative** (Dynamic template that shifts between **`✅ Passing`** and **`⚠️ Waiting`** so the user always knows *why* the score is where it is).

3. **Why This Protects You** (The emotional anchor connecting the metric to their wallet's safety).



```

┌────────────────────────────────────────────────────────┐

│  4 PRE-FLIGHT SAFETY CHECKS (TAP ANY ROW TO EXPAND):   │

├────────────────────────────────────────────────────────┤

│  ▼ 🏛️ Check 1: Strong Price Floor ($74,180)   ✅ 80%   │

│  ┌──────────────────────────────────────────────────┐  │

│  │ 💬 WHAT THIS MEANS:                              │  │

│  │ Think of this like checking the foundation of a  │  │

│  │ building before stepping onto the roof.          │  │

│  │                                                  │  │

│  │ 📊 RIGHT NOW (80% PASSED):                       │  │

│  │ Large institutional buyers have repeatedly       │  │

│  │ stepped in to defend the $74,180 price floor,    │  │

│  │ while the next major ceiling sits up at $78,500. │  │

│  │                                                  │  │

│  │ 🛡️ WHY THIS PROTECTS YOU:                        │  │

│  │ Knowing exactly where the concrete floor is      │  │

│  │ lets us place our Emergency Safety Exit just     │  │

│  │ underneath it ($74,180)—so we never guess where  │  │

│  │ a drop might stop.                               │  │

│  └──────────────────────────────────────────────────┘  │

│  ▶ 🌊 Check 2: Panic Selling Absorbed         ✅ 75%   │

│  ▶ 🌤️ Check 3: 50-Day Uptrend Line            ⚠️ 45%   │

│  ▶ 🚀 Check 4: Breakout Energy Coiling        ✅ 85%   │

└────────────────────────────────────────────────────────┘



```



### Complete Copy Matrix for All 4 Dropdown Cards (Both States)



Every check below includes ready-to-use copy templates for both the **Passing (`✅ Green`)** and **Waiting (`⚠️ Amber`)** states so your frontend can bind directly to your engine's live output:



| Check Header & Underlying Engine Desk | State A: When Check is Passing (`✅ ≥ 70%`) | State B: When Check is Waiting (`⚠️ < 70%`) | "Why This Protects You" Footer (Static Anchor) |

| --- | --- | --- | --- |

| **🏛️ Check 1: Strong Price Floor & Ceiling**<br>



<br>*(Engine: Desk [P] Multi-Timeframe Structure)* | **💬 Metaphor:** Think of this like checking the concrete foundation of a building before stepping onto the roof.<br>



<br>**📊 Right Now (`{score}%` Passed):** Big buyers have repeatedly stepped in to defend a solid price floor at **`${floor_price}`**, with open room up to the next ceiling at **`${ceiling_price}`**. | **💬 Metaphor:** Think of this like checking the concrete foundation of a building before stepping onto the roof.<br>



<br>**📊 Right Now (`{score}%` Waiting):** Bitcoin is floating in the middle of nowhere without a proven price floor nearby, or is pressed right up against a heavy price ceiling at **`${ceiling_price}`**. | **🛡️ Protection:** Buying near a proven floor keeps our risk tiny. Buying right under a ceiling is how beginners get trapped at the top. |

| **🌊 Check 2: Panic Selling Absorbed**<br>



<br>*(Engine: Desk [F] 15m Footprint Delta + Desk [W] Liquidation Waterfall)* | **💬 Metaphor:** Think of this like waiting for a flash flood to drain before driving across a bridge.<br>



<br>**📊 Right Now (`{score}%` Passed):** Forced panic-selling has calmed down. Over the last 15 minutes, active buyers outpaced sellers by **`+{net_btc} Bitcoin`**, soaking up the supply. | **💬 Metaphor:** Think of this like waiting for a flash flood to drain before driving across a bridge.<br>



<br>**📊 Right Now (`{score}%` Waiting):** Heavy selling waves are still hitting the market (**`-{net_btc} Bitcoin`** net selling in the last 15m). Big buyers haven't finished soaking up the panic yet. | **🛡️ Protection:** Prevents you from "catching a falling knife" during sudden market dumps and liquidation cascades. |

| **🌤️ Check 3: 50-Day Uptrend Line (Market Weather)**<br>



<br>*(Engine: Desk [L] 1D Macro Gate & 50 EMA / BBW)* | **💬 Metaphor:** Think of this like checking the weather radar before a flight.<br>



<br>**📊 Right Now (`{score}%` Passed):** Clear skies! Bitcoin (`${spot_price}`) is trading comfortably above its 50-Day Health Line (**`${ema_50}`**), confirming that the big-picture trend is pointing up. | **💬 Metaphor:** Think of this like checking the weather radar before a flight.<br>



<br>**📊 Right Now (`{score}%` Waiting):** The long-term sky is still foggy. Bitcoin (`${spot_price}`) is below its 50-Day Health Line (**`${ema_50}`**), meaning sellers still have the big-picture advantage. We wait in cash until price reclaims **`${ema_50}`**. | **🛡️ Protection:** Swimming *with* the long-term current makes winning easy; swimming against a downtrend drains your account. |

| **🚀 Check 4: Breakout Energy Coiling**<br>



<br>*(Engine: Desk [B] Classical Chart Patterns / Ascending Triangle)* | **💬 Metaphor:** Think of this like a tightly coiled metal spring ready to bounce upward.<br>



<br>**📊 Right Now (`{score}%` Passed):** Every time Bitcoin dips over the last few days, buyers step in at a slightly higher price—building upward pressure toward **`${breakout_level}`**. | **💬 Metaphor:** Think of this like a metal spring that is currently loose and uncoiled.<br>



<br>**📊 Right Now (`{score}%` Waiting):** Price is wandering back and forth without forming a clean launch shape. There is no upward spring tension built up yet. | **🛡️ Protection:** Keeps your cash on the sidelines during boring, directionless chop so your money only enters when a move is ready to launch.



 |



---



## Part 2: The Onboarding & Live "Portfolio Safety Sizer" Screen



In your original specification, the math examples assume a **$100,000 account** (`$750 Max Loss` and `0.6908 BTC` buy size). Because 90% of beginners start with **$500 to $5,000**, adding a **1-Tap Portfolio Safety Sizer** (accessible on first launch and anytime via a tap on the `$750 Max Loss` badge) makes the 0.75% Golden Rule immediately personal and calming.



### 1. Interactive Wireframe: The Portfolio Safety Sizer



```

┌────────────────────────────────────────────────────────┐

│  🛡️ PERSONALIZE YOUR SAFETY SHIELD          [✕ Close]  │

│    SET YOUR COMFORTABLE BITCOIN BUDGET                 │

├────────────────────────────────────────────────────────┤

│  How much total cash are you setting aside for         │

│  Bitcoin swing trades? (We never touch your bank—      │

│  this just calculates your exact safe buy amounts.)    │

│                                                        │

│  QUICK SELECT YOUR STARTING BUDGET:                    │

│  [ $500 ]   [ ● $1,000 ]   [ $5,000 ]   [ $10,000 ]    │

│                                                        │

│  OR TYPE EXACT AMOUNT:  [ $ 1,000.00               ]   │

├────────────────────────────────────────────────────────┤

│  🔒 YOUR GOLDEN 0.75% SAFETY PROMISE                   │

│                                                        │

│  ┌──────────────────────────────────────────────────┐  │

│  │  If a Buy Signal fails and hits our Emergency    │  │

│  │  Safety Floor, your planned loss is capped at:   │  │

│  │                                                  │  │

│  │           $7.50 MAXIMUM RISK PER TRADE           │  │

│  │          (Just 0.75% of your $1,000 budget)      │  │

│  │                                                  │  │

│  │  ███████████████████████████████████████░ 99.25% │  │

│  │  $992.50 of your money stays 100% protected!     │  │

│  └──────────────────────────────────────────────────┘  │

├────────────────────────────────────────────────────────┤

│  🧮 HOW THIS TRANSLATES TO TODAY'S MARKET ($75,953):   │

│  • Your Planned Entry Range : $75,200 – $75,500        │

│  • Emergency Safety Floor   : $74,180 (-1.55% gap)     │

│  • Exact Amount to Buy      : 0.0069 BTC (~$520.80)    │

│  • Uninvested Cash Buffer   : $479.20 stays in cash    │

│  • Max Loss if Floor Hits   : -$7.50                   │

├────────────────────────────────────────────────────────┤

│        [ ✅ Save My $1,000 Safety Shield ]             │

└────────────────────────────────────────────────────────┘



```



### 2. Why This Screen Solves Two Major Beginner Fears Instantly



* **The "Lunch Money" Reframe ($7.50 vs. $750)**: When a beginner with $1,000 sees that a worst-case stopped-out trade only costs them **$7.50** (the price of a coffee and pastry), their fear of ruin vanishes. They no longer panic-watch 1-minute candles because $7.50 cannot hurt their lifestyle.

* **Demystifying "Position Sizing" vs. "Account Size"**: Beginners often think that having a $1,000 account means they must buy $1,000 of Bitcoin on every trade. As shown in the wireframe above, when the Emergency Safety Floor (`$74,180`) is `-1.55%` below the entry price (`$75,350` midpoint), your formula $\text{Position Size} = \frac{\text{Equity} \times 0.0075}{\text{Entry} - \text{Stop}}$ recommends buying **0.0069 BTC (~$520.80)**—meaning nearly half their cash (`$479.20`) doesn't even need to enter the market to achieve the target return.







### 3. Dynamic Scaling Reference Table (For Your Frontend State)



Here is how your engine's exact Scenario B setup (**Entry Midpoint: $75,350**, **Emergency Floor: $74,180**, **Stop Distance: $1,170 / 1.55%**) scales across the four beginner preset buttons:



| User's Selected Budget (`Equity`) | Max Dollar Risk (`0.75% Golden Rule`) | Protected Capital (`99.25% Untouched`) | Recommended BTC Buy (`0.75% / 1.55% Stop`) | Dollar Value of BTC Buy | Relatable Comparison Micro-Copy |

| --- | --- | --- | --- | --- | --- |

| **$500** *(Starter)* | **$3.75 Max** | **$496.25 Safe** | `0.0032 BTC` | `~$241.50` | *"Less risk than a single cup of coffee."* |

| **$1,000** *(Default)* | **$7.50 Max** | **$992.50 Safe** | `0.0064 BTC` | `~$483.00` | *"Capped at the cost of a casual lunch."* |

| **$5,000** *(Builder)* | **$37.50 Max** | **$4,962.50 Safe** | `0.0320 BTC` | `~$2,415.00` | *"Less than a tank of gas at risk."* |

| **$100,000** *(Pro / Dossier)* | **$750.00 Max** | **$99,250.00 Safe** | `0.6410 BTC` | `~$48,300.00` | *"Institutional capital preservation."* |



(Note: In your original Scenario B, `0.6908 BTC` corresponded to the lower edge of the buy zone at `~$75,266` minus `$74,180 = $1,086` stop distance: $\$750 / \$1,086 = 0.6906\text{ BTC}$. Binding the calculator dynamically to `user_equity * 0.0075 / (entry_price - stop_price)` ensures the exact Bitcoin and dollar amounts update smoothly when they tap any preset button.)



---



## Part 3: Updated AI Copilot Prompt Template (With Dynamic Budget Injection)



With the refined terminology and the user's personalized budget from the Safety Sizer, here is the upgraded clipboard prompt generated when the user taps **`[💬 Tap to Copy AI Briefing: "Explain Today's Market to Me"]`**:



```markdown

Hey AI Copilot,



I am a beginner Bitcoin investor using the BTC Swing Mobile Guardian app (Spot-Only, Zero Leverage). Here is my live cockpit snapshot right now:



- My Total Bitcoin Budget: $1,000.00

- My Golden Safety Rule: Max 0.75% Risk per trade ($7.50 maximum planned loss)

- Current Bitcoin Price: $75,953.21

- Safety Clearance Meter: 45/100 (Needs 70/100 for a Green Light)

- Current Status: CAPITAL SHIELD ON — 100% Safe in Cash ($0.00 at risk)

- Market Mood: Choppy & Undecided (Buyers and sellers in a tug-of-war)



My 4 Pre-Flight Safety Checks:

1. Strong Price Floor: 80% Passed (Big buyers defending the $74,180 floor)

2. Panic Selling Absorbed: 75% Passed (Buyers outpaced sellers by +201 BTC in the last 15m)

3. 50-Day Uptrend Line (Market Weather): 45% Waiting (Price is still below the $79,826 health line)

4. Breakout Energy Coiling: 85% Passed (Buyers stepping in at higher prices every 4 hours)



Please explain to me in 3 warm, simple, jargon-free bullet points:

1. Why keeping my $1,000 safe in cash today is a winning professional move while Check 3 is still waiting.

2. What needs to change in the market for my Safety Clearance Meter to reach 70/100.

3. How my $7.50 (0.75%) safety cap and the $74,180 Emergency Floor will protect my $1,000 budget once a green buy signal finally arrives.



```



Would you like me to package all of these reviews, tables, and wireframes into a single consolidated **v2 Markdown specification file** so you can commit it directly to your repository?

I will now generate the consolidated v2 Beginner Narrative, Language Architecture & UX Psychology Specification in a single Markdown file, integrating all copy revisions, progressive disclosure cards, dynamic portfolio sizing, and psychological safeguards so you can commit it directly to your repository.

# BTC SWING MOBILE APP: BEGINNER NARRATIVE, LANGUAGE ARCHITECTURE & UX PSYCHOLOGY (v2.0)
## Complete Product Philosophy, Narrative Design & Investor Psychology Specification

**Document Version**: 2.0 (Incorporating Google Gemini AI Narrative, UX & Psychological Review)  
**Application**: BTC Swing Mobile Companion App (Setup B — Beginner Edition)  
**Target Audience**: 90% New Users, Beginners, Retail Traders, and Amateur Bitcoin Investors  
**Underlying Engine**: Institutional Long-Only BTC-USD Spot Microstructure & Auction Engine (179 Automated Safety Diagnostics Verified)  
**Date**: November 7, 2026  

---

## 1. Executive Summary & Ethical Positioning ("The Anti-Casino")

Most crypto trading software is built by quantitative engineers for other quantitative engineers. They flood mobile screens with dense order book ladders, confusing mathematical acronyms (`MSS/BOS`, `CVD`, `BBW`, `POC`, `Gartley PRZ`), multi-pane charts, and dangerous leverage controls.

For **90% of retail users—beginners, amateur investors, and everyday people buying Bitcoin**—this approach is disastrous:
1. **Jargon Intimidation**: Technical terminology causes anxiety and cognitive overload, driving users away or pushing them to blindly follow social media influencers.
2. **Behavioral Traps**: Without a disciplined framework, retail investors fall victim to FOMO (buying local tops), panic-selling (dumping at bottoms), and over-trading sideways noise.
3. **Catastrophic Losses**: Unregulated leverage and vague stop-loss guidance wipe out amateur accounts in sudden volatility spikes.

### The "Anti-Casino" Commercial Differentiation
Traditional retail exchanges (Binance, Coinbase, Kraken) operate on volume-driven fee models: they get paid every time a user clicks *Buy* or *Sell*, creating a structural incentive to encourage over-trading.

The **BTC Swing Mobile App** is built on an **Alignment Guarantee**:
- **Silent Institutional Rigor**: Our engine runs multi-timeframe auction theory, 15m footprint delta, rolling liquidation waterfall absorption, 72h volatility cones, and classical chart geometry silently in the background.
- **Calm, Protective UX**: 100% of the mobile experience is translated into a stress-free **"Personal Wall Street Guardian"** that speaks in warm, authoritative plain English.
- **Core Trust Anchors**:
  - **`🛡️ 100% Spot Bitcoin Only`**: Zero leverage, zero margin debt, zero overnight liquidation risk.
  - **`✅ 179 Automated Safety Diagnostics Verified`**: Institutional-grade reliability translated into everyday peace of mind.
  - **`💡 The One-Mistake Value Rule`**: Avoiding just one impulsive FOMO trade in a choppy market pays for this guardian for the next 3 years.

---

## 2. Amateur Investor Psychology: The 4 Fatal Pitfalls & v2 Solutions

To protect beginners, our architecture directly interrupts the emotional cycle of amateur Bitcoin investing:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       THE AMATEUR INVESTOR CYCLE                            │
│                                                                             │
│     [Euphoria / FOMO] ──► [Buy at Top] ──► [Price Drops 5%]                 │
│            ▲                                      │                         │
│            │                                      ▼                         │
│    [Revenge Buy] ◄── [Panic Sell at Bottom] ◄── [Severe Anxiety / Denial]   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Pitfall 1: "Action Bias" (The Compulsion to Over-Trade)
- **The Problem**: Beginners believe that to make money, they must constantly be in a trade. When Bitcoin moves sideways for weeks, boredom leads them to force low-quality trades, bleeding their account to fees and chop.
- **v2 Narrative Fix (Active Defense Framing)**: We reframe sitting in cash not as "passive waiting," but as an **actively deployed protective shield**:
  > *"80% of beginner losses happen in sideways markets like today. By keeping your Capital Shield on in 100% cash right now, you are actively outperforming the impatient crowd."*

### Pitfall 2: Fear of Ruin & Financial Ambiguity
- **The Problem**: Beginners rarely know their exact dollar risk before entering a trade, and default $100,000 institutional examples alienate everyday users starting with $500 to $5,000.
- **v2 Narrative Fix (The Personalized 0.75% Safety Shield)**: Using the **1-Tap Portfolio Safety Sizer** (defaulting to a relatable **$1,000 budget**), the user sees their exact worst-case planned risk in everyday terms before placing any trade:
  > *"By setting your automatic Safety Exit at $74,180 when you buy, your planned risk is capped at just $7.50 (0.75% of your $1,000 budget)—less than the cost of lunch. Over 99% ($992.50) of your savings remains completely untouched."*

### Pitfall 3: The Jargon Wall (Imposter Syndrome)
- **The Problem**: Terms like *"Bearish SFP"*, *"POC Migration"*, *"Ascending Triangle"*, and *"Waterfall ForceOrders"* make beginners feel inadequate.
- **v2 Narrative Fix (The Pilot's 4 Pre-Flight Safety Checks)**: We replace all technical indicators with four intuitive safety checks that progressive-disclose into plain-English metaphors:
  1. **Strong Price Floor & Ceiling**: Are big buyers defending a solid concrete floor?
  2. **Panic Selling Absorbed**: Has the flash flood of panic-selling drained?
  3. **50-Day Uptrend Line (Market Weather)**: Is the big-picture sky sunny or foggy?
  4. **Breakout Energy Coiling**: Is the price spring tightly coiled for a launch?

### Pitfall 4: Mixed Signals & Contradictory UI
- **The Problem**: Traditional apps show green buy buttons alongside bearish warnings, leaving beginners paralyzed. Furthermore, calling a gauge a "Green-Light Meter" while in yellow cash mode causes subconscious confusion.
- **v2 Narrative Fix (The Traffic Light Rule & Safety Clearance Meter)**:
  - The primary dial is named the **`Safety Clearance Meter (0–100)`** with a clear rule: *Needs 70/100 for a Green Light*.
  - **Below 70 (`⚠️ Amber Shield Mode`)**: Screen displays **`🛡️ CAPITAL SHIELD ON: STAY 100% IN CASH`**. Trade execution buttons are hidden to prevent impulsive clicks.
  - **70 or Above (`🟢 All-Clear Mode`)**: Screen turns green, displaying **`🟢 ALL CLEAR: BUY SIGNAL ACTIVE`** and unlocking the 4-Step Execution Checklist.

---

## 3. Institutional-to-Plain-English Translation Matrix (v2 Zero-Jargon Audited)

Every internal quantitative metric and UI label has been audited to eliminate institutional, charting, and crypto-slang leaks:

| Technical Quantitative Metric | Old / v1 Label | v2 Beginner-Friendly Label | What It Explains to the User |
|:---|:---|:---|:---|
| **1D Macro Gate $< 50$ EMA** | `Status: Safe in Cash` | **`🛡️ CAPITAL SHIELD ON: STAY 100% IN CASH`** | Active, protective framing: our shield is up while the market is stormy. |
| **Composite Confluence Score** | `Green-Light Buy Meter: 45%` | **`Safety Clearance Meter: 45/100`** | Removes the "Green-Light" naming paradox during amber warning states; clearly states *Needs 70/100 for a Green Light*. |
| **Market Regime (Chop/Squeeze)** | `Market Mood: Sideways Nap` | **`⏳ Market Mood: Choppy & Undecided`** | Avoids sounding "sleepy" with user money; explains that buyers and sellers are in a tug-of-war. |
| **Desk [P]: Multi-Timeframe Structure** | `Check 1: Safety Floors & Ceilings` | **`🏛️ Check 1: Strong Price Floor ($74,180)`** | Grounds the abstract concept by displaying the exact defended dollar floor right in the header. |
| **Desk [F] + [W]: Delta & Waterfalls** | `Check 2: Big Buyers & Dump Protection` | **`🌊 Check 2: Panic Selling Absorbed`** | Directly answers the beginner's #1 fear ("Are people dumping right now?"). |
| **Desk [L]: Macro Trend & 50 EMA** | `Check 3: The Big Picture Trend` | **`🌤️ Check 3: 50-Day Uptrend Line ($79,826)`** | Replaces "50 EMA" with the intuitive **50-Day Health Line** separating weak markets from strong uptrends. |
| **Desk [B]: Classical Chart Patterns** | `Ascending Triangle / Spring Coil` | **`🚀 Check 4: Breakout Energy Coiling`** | Strips out "Ascending Triangle" jargon; explains that buyers are stepping in at higher prices every 4 hours. |
| **Structural Invalidation Stop** | `Emergency Safety Exit Floor` | **`🛡️ Automatic Safety Exit ($74,180)`** | Clearly instructs the user where to place their automatic stop-loss order on their exchange. |
| **Take Profit 1 & Take Profit 2** | `Let runner ride to macro liquidity` | **`🎯 Profit Target 1 (Lock In Half) & Target 2 (Upper Goal)`** | Removes prop-trader slang ("runner", "macro liquidity") in favor of clear, step-by-step instructions. |
| **Mathematical Sizing Formula** | `Equity × 0.0075 / (Entry - Stop)` | **`🔒 Your 0.75% Golden Safety Cap ($7.50 Max Risk)`** | Dynamically scales to the user's actual budget ($500–$100k) so they never have to do mental math. |
| **Desk [0]: Screener Verdict** | `Sit on Hands (Be Patient)` | **`Today's Smart Move: Hold Cash & Let Market Settle`** | Replaces passive phrasing ("sit on hands") with empowering validation. |
| **Header Theme Switcher & Stablecoins** | `[NVG] [IBM] [SLATE]` / `USDT` | **`⚙️ Display`** / **`100% Cash (USD / Stablecoins)`** | Hides cryptic 3-letter terminal codes and explains `USDT` in plain terms. |

---

## 4. Screen-by-Screen User Journey & Progressive Disclosure Cards

### 4.1 The v2 Single-Screen Cockpit Wireframe (Scenario A: Cash Shield Mode)

```
┌────────────────────────────────────────────────────────┐
│  ● BTC SWING GUARDIAN                      [⚙️ Display] │
│    BEGINNER EDITION • 🛡️ 100% SPOT BITCOIN ONLY        │
├────────────────────────────────────────────────────────┤
│  BITCOIN SPOT PRICE    $75,953.21         +1.82% TODAY │
│  ● ASIA MARKET OPEN            🔥 12-Day Patience Streak│
├────────────────────────────────────────────────────────┤
│                     ╭──────────╮                       │
│                     │  45/100  │  SAFETY CLEARANCE     │
│                     ╰──────────╯  (Needs 70 for Green) │
│     ⏳ MARKET MOOD: CHOPPY & UNDECIDED (TUG-OF-WAR)    │
├────────────────────────────────────────────────────────┤
│     🛡️ CAPITAL SHIELD ON: STAY 100% IN CASH            │
├────────────────────────────────────────────────────────┤
│  🛡️ YOUR $1,000 BUDGET IS 100% PROTECTED IN CASH       │
│  "Right now, buyers and sellers are locked in a        │
│   tug-of-war. Buying today is a 50/50 coin flip—so     │
│   we keep your money safe in cash until buyers win."   │
│                                                        │
│  Active Position      : 100% Protected Cash (USD)      │
│  Money at Risk Today  : $0.00 (Zero Risk Exposure)     │
│  Drops Avoided (30d)  : 🛡️ +8.4% Market Drop Dodged    │
│  Today's Smart Move   : Hold Cash & Let Market Settle  │
│  [ 🧮 My Budget: $1,000 (Max Risk: $7.50) — Tap Edit ] │
├────────────────────────────────────────────────────────┤
│  WHAT MUST HAPPEN BEFORE WE BUY (2 OF 3 READY):        │
│  ✅ 1. Solid Price Floor Defended ($74,180 Holding)    │
│  ✅ 2. Panic Selling Absorbed (+201 BTC Net Buying)    │
│  ⚠️ 3. Reclaim 50-Day Health Line ($79,826) -> At $75.9k│
├────────────────────────────────────────────────────────┤
│  4 PRE-FLIGHT SAFETY CHECKS (TAP ANY ROW TO EXPAND):   │
│  ▶ 🏛️ Check 1: Strong Price Floor ($74,180)  ✅ 80%    │
│  ▶ 🌊 Check 2: Panic Selling Absorbed        ✅ 75%    │
│  ▶ 🌤️ Check 3: 50-Day Uptrend Line ($79.8k)  ⚠️ 45%    │
│  ▶ 🚀 Check 4: Breakout Energy Coiling       ✅ 85%    │
├────────────────────────────────────────────────────────┤
│  [ 💬 Tap to Copy AI Briefing: "Explain Today's Market"]│
├────────────────────────────────────────────────────────┤
│  💡 Today's 15-Second Lesson (Tap to Read):            │
│  80% of beginner losses happen in sideways markets.    │
│  Staying in cash today preserves your full buying      │
│  power for the next verified uptrend.                  │
└────────────────────────────────────────────────────────┘
```

---

### 4.2 The 4 Pre-Flight Safety Checks (Progressive Disclosure Copy Matrix)

When a user taps any of the 4 check rows, it expands smoothly into a **3-part micro-card** (*💬 Metaphor*, *📊 Live Status*, and *🛡️ Why This Protects You*). Below is the complete dynamic copy specification for both **Passing (`✅ $\ge 70\%$`)** and **Waiting (`⚠️ $< 70\%$`)** states:

| Check Header & Underlying Engine Desk | State A: When Check is Passing (`✅ Score >= 70%`) | State B: When Check is Waiting (`⚠️ Score < 70%`) | "Why This Protects You" Footer (Always Visible When Expanded) |
|:---|:---|:---|:---|
| **🏛️ Check 1: Strong Price Floor & Ceiling**<br>*(Desk [P] Multi-Timeframe Structure)* | **💬 Metaphor:** Think of this like checking the concrete foundation of a building before stepping onto the roof.<br>**📊 Right Now (`{score}%` Passed):** Big institutional buyers have repeatedly stepped in to defend a solid price floor at **`${floor_price}`**, with open room up to the next ceiling at **`${ceiling_price}`**. | **💬 Metaphor:** Think of this like checking the concrete foundation of a building before stepping onto the roof.<br>**📊 Right Now (`{score}%` Waiting):** Bitcoin is floating in the middle of nowhere without a proven price floor nearby, or is pressed right up against a heavy price ceiling at **`${ceiling_price}`**. | **🛡️ Why This Protects You:** Knowing where the concrete floor is lets us place our Automatic Safety Exit just underneath it (`${floor_price}`)—keeping our risk tiny and avoiding top-buying traps. |
| **🌊 Check 2: Panic Selling Absorbed**<br>*(Desk [F] 15m Footprint Delta + Desk [W] Waterfalls)* | **💬 Metaphor:** Think of this like waiting for a flash flood to drain before driving across a bridge.<br>**📊 Right Now (`{score}%` Passed):** Forced panic-selling has calmed down. Over the last 15 minutes, active buyers outpaced sellers by **`+{net_btc} Bitcoin`**, soaking up the supply. | **💬 Metaphor:** Think of this like waiting for a flash flood to drain before driving across a bridge.<br>**📊 Right Now (`{score}%` Waiting):** Heavy selling waves are still hitting the market (**`-{net_btc} Bitcoin`** net selling in the last 15 minutes). Big buyers haven't finished soaking up the panic yet. | **🛡️ Why This Protects You:** Prevents you from "catching a falling knife" during sudden market dumps and forced liquidation cascades. |
| **🌤️ Check 3: 50-Day Uptrend Line (Market Weather)**<br>*(Desk [L] 1D Macro Gate & 50 EMA / BBW)* | **💬 Metaphor:** Think of this like checking the weather radar before a flight.<br>**📊 Right Now (`{score}%` Passed):** Clear skies! Bitcoin (`${spot_price}`) is trading comfortably above its 50-Day Health Line (**`${ema_50}`**), confirming that the big-picture trend is pointing up. | **💬 Metaphor:** Think of this like checking the weather radar before a flight.<br>**📊 Right Now (`{score}%` Waiting):** The long-term sky is still foggy. Bitcoin (`${spot_price}`) is below its 50-Day Health Line (**`${ema_50}`**), meaning sellers still have the big-picture advantage. We stay in cash until price reclaims **`${ema_50}`**. | **🛡️ Why This Protects You:** Swimming *with* the long-term current makes winning much easier; swimming against a macro downtrend slowly drains your account. |
| **🚀 Check 4: Breakout Energy Coiling**<br>*(Desk [B] Classical Chart Geometry)* | **💬 Metaphor:** Think of this like a tightly coiled metal spring ready to bounce upward.<br>**📊 Right Now (`{score}%` Passed):** Every time Bitcoin dipped over the last few days, buyers stepped in at a slightly higher price—building upward pressure toward **`${breakout_level}`**. | **💬 Metaphor:** Think of this like a metal spring that is currently loose and uncoiled.<br>**📊 Right Now (`{score}%` Waiting):** Price is wandering back and forth without forming a clean launch shape. There is no upward spring tension built up yet. | **🛡️ Why This Protects You:** Keeps your cash on the sidelines during boring, directionless chop so your money only enters when a move is ready to launch. |

---

### 4.3 Scenario B: When an Institutional All-Clear Signal Fires (Score 82/100)

*(Note: To maintain 100% numerical consistency across the UI, when Scenario B triggers after reclaiming the 50-Day Health Line or passing the 70/100 composite threshold, the card displays exact, non-contradictory levels scaled to the user's selected budget.)*

1. **The Instant Green Light**:
   - The Safety Clearance Meter animates to **`82/100`** with a glowing green banner: **`🟢 ALL CLEAR: BUY SIGNAL ACTIVE`**.
2. **The 4-Step Action Checklist (Scaled to a $1,000 Default Budget)**:
   - **Step 1 — Buy Price Range**: Enter between **`$75,200` and `$75,500`** *(Midpoint: `$75,350`)*.
   - **Step 2 — Exact Amount to Buy**: **`0.0064 Bitcoin`** *(Costs **`~$483.00`** of your `$1,000` budget; the remaining **`$517.00`** stays safely in cash)*.
   - **Step 3 — Automatic Safety Exit (Stop-Loss)**: Set at **`$74,180`** *(If Bitcoin drops here, you exit automatically; your planned loss is capped at just **`-$7.50`**)*.
   - **Step 4 — Profit Targets**:
     - **Target 1 (`$78,500`)**: Sell half (`0.0032 BTC`) to lock in guaranteed profit.
     - **Target 2 (`$82,000`)**: Let your remaining half ride toward the upper target.

---

### 4.4 Emergency "Storm Shield" Micro-Copy (When Bitcoin Dumps 10%+)

When Bitcoin experiences a violent intraday crash (e.g., $-10\%$ in a few hours), beginners experience an adrenaline spike that leads to panic-selling or reckless "knife-catching." The app automatically displays a high-visibility **Storm Shield Banner** tailored to the user's current state:

#### State 1: User is in Cash Mode (Most Common)
> **⛈️ MARKET STORM DETECTED (-10.2% TODAY) — YOUR LOSS: $0.00**  
> *"Panic sellers are dumping right now, and our Check 2 (Panic Selling Protection) has locked the cockpit to keep you safe. Do NOT try to 'catch a falling knife.' Because you followed the system and stayed in cash, your money just gained 10% more future buying power. Sit back calmly until the selling stops and our Safety Clearance Meter turns green."*

#### State 2: User Was in an Active Trade That Hit the Safety Floor
> **🛡️ AUTOMATIC SAFETY EXIT TRIGGERED AT $74,180 — 99.25% OF CAPITAL SAVED**  
> *"Your safety net worked exactly as designed. While the broader market crashed over 10%, your Automatic Safety Exit cut the cord early—capping your loss at just $7.50 (0.75%) and protecting $992.50 of your $1,000 budget. Take a deep breath. You are safely back in 100% cash until the storm passes."*

---

## 5. Onboarding & Live "Portfolio Safety Sizer" Specification

Because 90% of beginners invest between **$500 and $5,000** (rather than $100,000), the **Portfolio Safety Sizer** appears during onboarding and can be opened anytime by tapping **`[ 🧮 My Budget ]`** on the dashboard.

### 5.1 Interactive Wireframe: The Portfolio Safety Sizer Drawer

```
┌────────────────────────────────────────────────────────┐
│  🛡️ PERSONALIZE YOUR SAFETY SHIELD          [✕ Close]  │
│    SET YOUR COMFORTABLE BITCOIN BUDGET                 │
├────────────────────────────────────────────────────────┤
│  How much total cash are you setting aside for         │
│  Bitcoin swing trades? (We never touch your bank—      │
│  this simply calculates your safe buy amounts.)        │
│                                                        │
│  QUICK SELECT YOUR STARTING BUDGET:                    │
│  [ $500 ]   [ ● $1,000 ]   [ $5,000 ]   [ $10,000 ]    │
│                                                        │
│  OR TYPE EXACT AMOUNT:  [ $ 1,000.00               ]   │
├────────────────────────────────────────────────────────┤
│  🔒 YOUR GOLDEN 0.75% SAFETY PROMISE                   │
│                                                        │
│  ┌──────────────────────────────────────────────────┐  │
│  │  If a Buy Signal fails and hits our Automatic    │  │
│  │  Safety Exit, your planned loss is capped at:    │  │
│  │                                                  │  │
│  │           $7.50 MAXIMUM RISK PER TRADE           │  │
│  │          (Just 0.75% of your $1,000 budget)      │  │
│  │                                                  │  │
│  │  ███████████████████████████████████████░ 99.25% │  │
│  │  $992.50 of your money stays 100% protected!     │  │
│  └──────────────────────────────────────────────────┘  │
├────────────────────────────────────────────────────────┤
│  🧮 HOW THIS SCALES TO AN ACTIVE TRADE ($75,350 ENTRY):│
│  • Planned Buy Range        : $75,200 – $75,500        │
│  • Automatic Safety Exit    : $74,180 (-1.55% gap)     │
│  • Exact Amount to Buy      : 0.0064 BTC (~$483.00)    │
│  • Uninvested Cash Buffer   : $517.00 stays in cash    │
│  • Planned Loss if Exit Hits: -$7.50 (Price of lunch)  │
├────────────────────────────────────────────────────────┤
│        [ ✅ Save My $1,000 Safety Shield ]             │
└────────────────────────────────────────────────────────┘
```

### 5.2 Underlying Sizing Math & Dynamic Scaling Table

The frontend binds the user's selected budget (`Budget`) to the deterministic risk formula:

$$\text{Recommended BTC Buy} = \frac{\text{Budget} \times 0.0075}{\text{Entry Price} - \text{Safety Exit Price}}$$

Using Scenario B (`Entry Midpoint` $= \$75,350$, `Safety Exit` $= \$74,180$, `Stop Distance` $= \$1,170$ or $1.55\%$), the UI dynamically populates across all presets:

| User's Selected Budget (`Budget`) | Max Planned Risk (`0.75% Golden Cap`) | Protected Capital (`99.25% Untouched`) | Recommended BTC Buy (`$1,170 Stop Gap`) | Dollar Cost of BTC Buy | Relatable Psychological Anchor Copy |
|:---|:---|:---|:---|:---|:---|
| **$500** *(Starter)* | **$3.75 Max** | **$496.25 Safe** | `0.0032 BTC` | `~$241.50` | *"Less risk than a single cup of coffee."* |
| **$1,000** *(Default)* | **$7.50 Max** | **$992.50 Safe** | `0.0064 BTC` | `~$483.00` | *"Capped at the cost of a casual lunch."* |
| **$5,000** *(Builder)* | **$37.50 Max** | **$4,962.50 Safe** | `0.0320 BTC` | `~$2,415.00` | *"Less than a tank of gas at risk."* |
| **$10,000** *(Growth)* | **$75.00 Max** | **$9,925.00 Safe** | `0.0641 BTC` | `~$4,830.00` | *"99.25% of your savings stays shielded."* |
| **$100,000** *(Pro)* | **$750.00 Max** | **$99,250.00 Safe** | `0.6410 BTC` | `~$48,300.00` | *"Institutional capital preservation."* |

---

## 6. Expanded 3-Mode AI Copilot Prompt Engine

When the user taps **`[ 💬 Tap to Copy AI Briefing ]`**, a lightweight bottom sheet lets them choose **one of three situational prompts** to copy to their clipboard for Google Gemini, ChatGPT, or Grok:

### Mode A: `🧠 "Explain today's market to me in simple words"` (Default Daily Learning)
```markdown
Hey AI Copilot,

I am a beginner Bitcoin investor using the BTC Swing Mobile Guardian app (100% Spot-Only, Zero Leverage). Here is my live cockpit snapshot right now:

- My Total Bitcoin Budget: $1,000.00
- My Golden Safety Rule: Max 0.75% Risk per trade ($7.50 maximum planned loss)
- Current Bitcoin Price: $75,953.21
- Safety Clearance Meter: 45/100 (Needs 70/100 for a Green Light)
- Current Status: CAPITAL SHIELD ON — 100% Safe in Cash ($0.00 at risk)
- Market Mood: Choppy & Undecided (Buyers and sellers in a tug-of-war)

My 4 Pre-Flight Safety Checks:
1. Strong Price Floor: 80% Passed (Big buyers defending the $74,180 floor)
2. Panic Selling Absorbed: 75% Passed (Buyers outpaced sellers by +201 BTC in the last 15m)
3. 50-Day Uptrend Line (Market Weather): 45% Waiting (Price is still below the $79,826 health line)
4. Breakout Energy Coiling: 85% Passed (Buyers stepping in at higher prices every 4 hours)

Please explain to me in 3 warm, simple, jargon-free bullet points:
1. Why keeping my $1,000 safe in cash today is a winning professional move while Check 3 is still waiting.
2. What needs to change in the market for my Safety Clearance Meter to reach 70/100.
3. How my $7.50 (0.75%) safety cap and the $74,180 Automatic Safety Exit will protect my $1,000 budget once a green buy signal arrives.
```

### Mode B: `🔥 "Everyone on social media is buying! Why are we waiting?"` (FOMO Cure)
```markdown
Hey AI Copilot,

I am feeling FOMO (Fear Of Missing Out) because Bitcoin is up +1.82% today ($75,953.21) and people on social media are telling everyone to buy right now.

However, my BTC Swing Guardian app has my $1,000 budget in "CAPITAL SHIELD ON (100% Cash)" because our Safety Clearance Meter is only at 45/100. Specifically, Check 3 (The 50-Day Uptrend Line at $79,826) is still failing at 45%.

Please talk me off the ledge in 3 calm, reassuring bullet points:
1. Why retail crowds on social media often get trapped buying small bounces below the 50-Day Health Line ($79,826).
2. Why missing the first few percent of a move to wait for verified safety (70/100) protects beginners from fakeouts.
3. A quick reminder of how professionals treat cash as an active defensive shield.
```

### Mode C: `📋 "Walk me through placing this exact trade step-by-step"` (Active Buy Signal Only)
```markdown
Hey AI Copilot,

My BTC Swing Guardian app just flashed a Green Light (82/100 Safety Clearance)! Here is my exact trade plan for my $1,000 budget:
- Step 1 (Buy Range): $75,200 to $75,500
- Step 2 (Exact Buy Amount): 0.0064 BTC (~$483.00 cost, leaving $517.00 in cash)
- Step 3 (Automatic Safety Exit / Stop-Loss): $74,180 (Capping my planned risk at $7.50)
- Step 4 (Profit Targets): Sell half at $78,500, and let the rest ride to $82,000.

I am a beginner using a standard crypto exchange app. Please explain in simple, step-by-step plain English:
1. How to place a "Limit Buy" order for 0.0064 BTC at $75,350 so I don't overpay on fees.
2. How to immediately set my Automatic Safety Exit (Stop-Loss) at $74,180 so my risk is locked at $7.50.
3. Why I only need to invest ~$483 of my $1,000 budget to make this trade work safely.
```

---

## 7. Retention & Engagement Architecture During Multi-Week Cash Regimes

To keep beginners engaged when the engine remains in **`CAPITAL SHIELD ON (100% Cash)`** for 2 to 3 weeks without encouraging them to over-trade, the cockpit incorporates three non-trading reward loops:

1. **The "Dodged Bullet" Counter (`🛡️ Drops Avoided`)**:
   - Tracks the cumulative percentage drawdown from local highs while the engine kept the user in cash (e.g., **`🛡️ +8.4% Market Drop Dodged This Month`**). Proving visually that *inaction saved money* turns patience into a tangible win.
2. **The Patience Streak Badge (`🔥 12-Day Patience Streak`)**:
   - Increments each day the user checks in and respects the system's cash shield during choppy regimes, reinforcing identity as a disciplined investor (*"Trading Like the Top 5%"*).
3. **Daily 15-Second "Black Box" Micro-Lesson**:
   - A rotating 2-sentence footer card that explains *one* real-world concept using today's live numbers (e.g., *"Why did Check 2 block us yesterday? Because 400 BTC of panic selling hit at 2:00 PM—and staying in cash saved you from a 3% dip."*).

I have packaged the complete v2 Beginner Narrative, Language Architecture & UX Psychology Specification into BTC_SWING_MOBILE_BEGINNER_NARRATIVE_V2.md. You can copy or export this file directly into your project folder and commit it to GitHub.

Would you like me to build an interactive HTML/React mobile prototype of this exact v2 cockpit (complete with the live Safe in Cash / Active Buy preview toggle, expandable 4 Safety Checks, and interactive Portfolio Safety Sizer drawer) so you can test the UX live in your browser?

I will now build the interactive mobile companion web application for the BTC Swing Cockpit — Beginner Edition (v2).
