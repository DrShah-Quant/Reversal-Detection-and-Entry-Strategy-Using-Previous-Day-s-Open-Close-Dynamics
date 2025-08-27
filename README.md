# Event-Driven Reversal Capture Strategy with NAV-Based Position Sizing

---

## 📌 Strategy Title
**Reversal Detection and Entry Strategy Using Previous Day's Open-Close Dynamics**

---

## 📖 Strategy Description

This trading strategy attempts to capture **reversal opportunities** based on the previous day’s candlestick movement.  
It compares the **open-close dynamics of the prior trading day** and uses the first tick of the current day to decide if a buy order should be placed.  

The position sizing is dynamically adjusted based on **10% of the available NAV**, ensuring risk-adjusted exposure.  

---

### 🔹 Steps Followed

1. **Initialization**
   - Subscribes to instruments defined in the trading environment.  
   - Tracks:
     - Daily open and close prices.  
     - Previous day’s open and close prices.  
     - NAV (Net Asset Value).  
     - Open positions, pending orders, and current prices.  
   - Resets state variables at the start of each new trading day.

2. **End-of-Day (EOD) Handling**
   - At the start of a new day, the previous day’s **open** and **close** prices are stored.  
   - Today’s open/close placeholders are reset for the fresh trading day.  

3. **Market Data Handling**
   - For each instrument:
     - Updates **today’s open** (first tick of the day) and **today’s close** (latest tick).  
     - Skips redundant processing after the first tick per day.  

4. **Reversal Signal Generation**
   - Calculates previous day’s percentage change:
   - 
      $\text{ChangePct} = \dfrac{\text{PrevClose} - \text{PrevOpen}}{\text{PrevOpen}} \times 100$

   - If the previous day dropped **more than -3%**:
     - Calculates the drop amount (`PrevOpen - PrevClose`).  
     - Sets a **buy trigger price** = `PrevClose + 0.52 × drop_amt`.  
     - If today’s opening price is between this trigger price and previous open, a buy is triggered.  
   - If the previous day rose **more than +3%**:
     - Calculates the rise amount (`PrevClose - PrevOpen`).  
     - Sets a **buy trigger price** = `PrevOpen + 0.52 × rise_amt`.  
     - If today’s opening price is between this trigger price and previous close, a buy is triggered.  

5. **Trade Execution**
   - On a valid trigger:
     - Creates an order with:
       - **Buy side**  
       - Volume = `10% of NAV ÷ current price` (integer)  
       - **Take-Profit level**:
         - If prior drop: `PrevOpen × 1.0005`  
         - If prior rise: `PrevClose × 1.0005`  
       - **Trailing stop** = 0.0003  
       - **Time-in-force** = 3600 seconds (1 hour)  
     - Sends order to execution system.  
   - Logs order details (instrument, price, volume, TP, trailing stop, NAV, etc.).

---

### 📊 Trading Interpretations

- **Prev Day Drop > -3% (Oversold Rebound Setup)**  
  - Market is considered oversold.  
  - A buy is triggered when today’s price begins recovering from the previous day’s close.  
  - Target is a quick rebound toward the previous open.  

- **Prev Day Rise > +3% (Continuation/Pullback Setup)**  
  - Market shows strong momentum.  
  - A buy is triggered if today’s price holds above a key retracement level (52% of the prior rise).  
  - Target is continuation toward the previous close.  

- **NAV-Based Position Sizing**  
  - Exposure scales with account balance, keeping risk proportionate.  

- **Stop/Exit Logic**  
  - Take-Profit set just above prior open/close.  
  - Tight trailing stop (0.0003) locks in profits quickly in volatile conditions.  

⚠️ *Note: The strategy only looks for **buy entries**. It assumes that post-drop rebounds and post-rise continuations are profitable setups. It does not generate short signals.*  

---

## 🛠️ Libraries Used

- **AlgoAPI**  
  - `AlgoAPIUtil`, `AlgoAPI_Backtest`  
  - Provides event-driven trading and backtesting framework.  

- **datetime**  
  - `datetime`  
  - Used to track trading days and detect end-of-day resets.  

- **uuid**  
  - `uuid`  
  - Provides unique identifiers for tracking orders or trades (not fully used in current code).  

