# Ablation + Walk-Forward Implementation Roadmap (Steps 3 & 4)

## Scope and Decisions (Current Choices)

### Step 3 (Component Ablation Testing)
- **Scope**: implement **ablation matrix execution only** in `run_ablation.py`.  

- **Ablation design**: **hybrid matrix** = OAT baseline + selected combinations (not full 2^N).

### Step 4 (Walk-Forward Optimization)

- **WFO scheme**: Rolling windows (fixed train, fixed test).

- **Selection objective**: support both
  - Max Sharpe
  - Return − λ · Drawdown

### Reporting
- Preferred final report format: **LaTeX tables** (paper-ready).  
  Recommendation: also output **CSV/JSON** as canonical run artifacts, then compile LaTeX from these.

---

## Step 3 — `src/cli/run_ablation.py` Enhancement Plan

### 3.1 Ablation Matrix Construction (Hybrid)
The hybrid design should include:

1) **Full-on baseline**
- All components enabled (`true`)

2) **OAT baseline set**
- Disable one component at a time (N configs)

3) **Selected combinations**
- Default recommendation: **pairwise ablation coverage**
  - either (a) disable pairs (to test redundancy)
  - and/or (b) enable pairs starting from all-off (to test synergy)
- This yields strong insight into interactions at a fraction of the full 2^N cost.


---


### 3.4 Metrics to Collect (Minimum Set)
**Performance**
- Total return
- Sharpe ratio

**Risk**
- Volatility
- Max drawdown

**Trading activity**
- Number of trades
- Average holding period


**Comparisons**
- Delta vs full-on baseline for key metrics (e.g., ΔSharpe, ΔReturn, ΔMDD)

---

## Step 4 — Walk-Forward Workflow (Outlined for a Separate Script)


### 4.1 `src/cli/run_walkforward.py` (Placeholder Plan)
**Rolling walk-forward scheme**
- Train/optimization window length: `T_train`
- Test window length: `T_test`
- Windows roll forward by `T_test` (or a smaller step if desired later)

For each split k:
1. define train period 
2. define test period  
3. optimize parameters on train
4. evaluate chosen params on test
5. append OOS results to a concatenated OOS equity series

### 4.2 Optimization Objective
Provide two objective modes:
- `objective = sharpe`
- `objective = return_minus_lambda_dd` with a config parameter `lambda_dd`

Note: the mechanism used to search parameters (grid/random/bayes) is explicitly delegated to a separate research/design task.

---

**Ablation tables**
- Table: configurations × key metrics (Return, Sharpe, MDD, Trades)
- Table: deltas vs baseline (ΔReturn, ΔSharpe, ΔMDD)

**Interaction-focused tables (for hybrid/pairwise)**
- Pairwise effect table (e.g., disable two components) to highlight synergy/redundancy
- Optional: rank components by average marginal contribution (computed over sampled configs)

**Figures (optional but recommended)**
- Heatmap (configs × metric deltas) exported as PDF/PNG and included via `\includegraphics`
- For WFO later: OOS concatenated equity curve plot

---
