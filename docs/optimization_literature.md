# Literature Review: Parameter Optimization for Trading Strategies

## 1. Executive Summary
This document reviews prominent parameter optimization methods with a specific focus on their application to algorithmic trading. It compares their computational efficiency and suitability for financial time series.

## 2. Research Methods Overview

### 2.1 Grid Search
* **Description:** Iterates through a manually specified "grid" of numbers.
* **Trading Context:** Good for simple strategies (1-2 parameters) to visualize landscapes. Too slow for complex strategies.

### 2.2 Random Search
* **Description:** Samples parameter combinations randomly.
* **Trading Context:** Often outperforms Grid Search in high dimensions because it doesn't waste time on irrelevant parameters.

### 2.3 Bayesian Optimization (Recommended)
* **Description:** A smart model that "learns" from previous tests to predict where the best parameters might be.
* **Trading Context:** Highly efficient. It finds the best profit with fewer backtests compared to Grid or Random search.

### 2.4 Genetic Algorithms (GA) & Particle Swarm (PSO)
* **Description:** Inspired by biology (evolution) or nature (flocking birds).
* **Trading Context:** Excellent for complex rules or "rugged" landscapes, but harder to tune.

## 3. Comparative Analysis

| Method | Speed | Pros | Cons |
| :--- | :--- | :--- | :--- |
| **Grid Search** | Slow | Simple, complete coverage of the grid. | Inefficient, curse of dimensionality. |
| **Random Search** | Medium | Unbiased, better for high dimensions. | No guarantee of finding the best spot. |
| **Bayesian Opt** | **Fast** | Very sample-efficient, smart exploration. | Complex to implement manually (needs libraries like Optuna). |

## 4. Conclusion
For our strategy, we will prioritize **Bayesian Optimization** (via the Optuna library) due to its balance of speed and accuracy. We will use **Grid Search** only for generating Heatmaps during the sensitivity analysis phase.