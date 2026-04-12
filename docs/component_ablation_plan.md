# Component Ablation Testing Plan

## Objective

The objective of this ablation study is to systematically evaluate the contribution and interaction effects of individual strategy components by testing different combinations of enabled and disabled modules. The approach is designed to measure not only isolated component effects, but also higher-order interactions and correlations between components.

All components are controlled via binary ablation flags defined in `configs/base.yaml`.

---

## Strategy Components Under Analysis

The following strategy components are included in the ablation study:

- **RSI Entry Filter** (`use_rsi`)
- **Hurst Filter** (`use_hurst`)
- **Time-Based Exit** (`use_time_exit`)
- **RSI Exit** (`use_RSI_exit`)
- **Take Profit Mechanism** (`use_take_profit`)

Each component can be independently enabled (`true`) or disabled (`false`), allowing for systematic exploration of the strategy design space.

---

## Ablation Matrix Construction

### Full Combinatorial Ablation Matrix

To capture both individual and interaction effects, a **full combinatorial ablation matrix** is constructed.  
With \( N = 5 \) binary components, the total number of configurations is:

\[
2^N = 32
\]

Each row in the matrix corresponds to a unique combination of enabled and disabled components. This design allows:

- estimation of **main effects** of each component,
- identification of **interaction effects** between components,
- analysis of **component dependency and correlation structures**.

An example row of the ablation matrix:

| use_rsi | use_hurst | use_time_exit | use_RSI_exit | use_take_profit |
|--------:|----------:|--------------:|-------------:|----------------:|
| true    | false     | true          | false        | true            |

---

### One-at-a-Time (OAT) Ablation as Baseline

In addition to the full matrix, a **one-at-a-time (OAT)** ablation is used as a baseline comparison.  
In this setup, each component is disabled individually while keeping all others enabled.

OAT ablation provides:
- intuitive interpretation of marginal effects,
- reduced computational cost,
- a reference point for validating results from the full combinatorial matrix.

However, OAT does **not capture interaction effects** and may underestimate or misattribute component importance in the presence of non-linear dependencies.

---

## Metrics for Component Evaluation

Each configuration in the ablation matrix is evaluated using the following metrics:

### Performance Metrics
- Total return
- Sharpe ratio
- Performance delta relative to the full (all-components-enabled) configuration

### Risk Metrics
- Volatility
- Maximum drawdown
- Risk-adjusted performance changes

### Trading Activity Metrics
- Trade count
- Changes in trade frequency

These metrics allow disentangling whether a component primarily affects profitability, risk exposure, or trading behavior.

---

## Analysis of Effects and Correlations

The full ablation matrix enables:

- **Marginal effect estimation**: average performance change when a component is enabled vs disabled across all configurations.
- **Interaction analysis**: identification of component pairs or groups whose combined effect differs from the sum of individual effects.
- **Correlation analysis**: detection of components that systematically co-contribute to performance or risk outcomes.

This approach provides a more robust understanding of strategy structure compared to isolated ablation tests.

---

## Expected Outcomes

The ablation study is expected to:
- identify components with consistently positive or negative contributions,
- reveal redundant or highly correlated components,
- highlight components whose value depends strongly on the presence of others.

These insights support informed strategy simplification, robustness improvements, and principled feature selection.

---

## Notes on Practical Considerations

- All evaluations should be performed on identical data splits to ensure comparability.
- Results should be analyzed across multiple time periods to account for regime dependency.
- Statistical significance testing should be applied to performance differences where applicable.

