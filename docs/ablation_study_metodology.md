Perform ablation running the backtest using a different combination of the feature every time. Compute the metrics and then 
compute deltas on them. Also the number of completed trades is important. In this way we can observe both the individual contribute but also the intrection between the different features.

We could build an Ablation Matrix where every row is the list of True/False representing if a single feature is active or not.

I suggest not to include in the ablation process the "use hurst" and "use rsi", because the strategy would lose its sense (imo).

Moreover we could use SHAP for the sensitivity analisys.
