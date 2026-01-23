# Ablation Study Methodology

## Overview

Ablation studies are experimental techniques used to assess the contribution of individual components within a machine learning system by systematically removing or disabling them and measuring the resulting change in performance. They are widely applied to validate model architectures, feature sets, and pipeline components (Zeiler & Fergus, 2014).

In quantitative trading, ablation studies are commonly used to evaluate:
- individual alpha signals,
- groups of features (e.g. price-based, volume-based, macroeconomic),
- model submodules such as risk management or position sizing logic.

A key challenge in this domain is the presence of non-linear interactions and regime dependency, which can make naïve ablation results misleading (Bailey et al., 2014).

---

## Ablation Study Methodologies in Machine Learning and Trading

In machine learning research, ablation studies are a standard validation tool for understanding architectural choices and component necessity, particularly in deep learning models (Zeiler & Fergus, 2014; Hooker et al., 2019). Typical approaches include:
- single-component removal,
- grouped ablation (removing classes of features),
- progressive ablation (incremental removal).

In trading systems, ablation is often performed on backtest results. However, financial time series exhibit autocorrelation, non-stationarity, and feedback effects, requiring careful experimental design to avoid overfitting and false attribution of component importance (Bailey et al., 2014).

---

## Feature Importance Analysis Techniques

Feature importance methods can be viewed as a soft or probabilistic form of ablation:

- **Permutation Feature Importance**: measures the performance degradation when feature values are randomly permuted, breaking their association with the target (Breiman, 2001).
- **SHAP (SHapley Additive exPlanations)**: estimates the average marginal contribution of each feature across all possible feature coalitions, grounded in cooperative game theory (Lundberg & Lee, 2017).
- **Gradient-based attribution methods** (e.g. Integrated Gradients): assess model sensitivity to input features and are commonly used in deep neural networks (Sundararajan et al., 2017).

In financial applications, SHAP values are frequently preferred due to their theoretical grounding, although they are computationally expensive and rely on assumptions that may not fully hold in market data, such as conditional independence and stationarity.

---

## Component Contribution: Marginal vs Total Effects

Two main notions of contribution are commonly distinguished:

- **Marginal contribution**: the incremental performance change when a component is added to or removed from a baseline system.
- **Total contribution**: the overall effect of a component, including its interactions with other components.

Shapley-value-based methods provide a principled framework for marginal contribution attribution but assume expectation-based additivity and relative stationarity. These assumptions are often violated in trading systems due to feature correlation and regime shifts (Israelsen, 2015).

---

## Statistical Significance Testing for Component Removal

To assess whether performance differences observed during ablation are statistically significant, several techniques are used:

- **Diebold–Mariano tests** for comparing predictive accuracy across time series models (Diebold & Mariano, 1995),
- **Bootstrap and block bootstrap methods** to account for temporal dependence in financial returns (Efron & Tibshirani, 1993),
- **Deflated Sharpe Ratio** to correct for selection bias and multiple testing in backtests (Bailey & López de Prado, 2012).

Proper statistical testing is essential to avoid false positives, especially when evaluating large numbers of features or trading signals.

---

## References

- Bailey, D., Borwein, J., López de Prado, M., & Zhu, Q. (2014). *The Probability of Backtest Overfitting*. Journal of Computational Finance.
- Bailey, D., & López de Prado, M. (2012). *The Deflated Sharpe Ratio*. Journal of Portfolio Management.
- Breiman, L. (2001). *Random Forests*. Machine Learning.
- Diebold, F. X., & Mariano, R. S. (1995). *Comparing Predictive Accuracy*. Journal of Business & Economic Statistics.
- Efron, B., & Tibshirani, R. (1993). *An Introduction to the Bootstrap*. Chapman & Hall.
- Hooker, S. et al. (2019). *A Benchmark for Interpretability Methods in Deep Neural Networks*. NeurIPS.
- Lundberg, S. M., & Lee, S.-I. (2017). *A Unified Approach to Interpreting Model Predictions*. NeurIPS.
- Sundararajan, M., Taly, A., & Yan, Q. (2017). *Axiomatic Attribution for Deep Networks*. ICML.
- Zeiler, M. D., & Fergus, R. (2014). *Visualizing and Understanding Convolutional Networks*. ECCV.
- Israelsen, R. (2015). *A Refinement to the Sharpe Ratio and Information Ratio*. Journal of Asset Management.

