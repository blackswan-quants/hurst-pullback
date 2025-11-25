import yaml
from src.core.loader import load_data
from src.core.engine import run
from src.strategy.strategy import Strategy
import pandas as pd 
import copy
import logging
from src.core.metrics import sharpe_ratio, max_drawdown, cagr


def main() -> None:
    """
    Run ablation tests to isolate component contributions.
    Steps:
    1. Iterate over all ablation flags.
    2. Disable one component at a time.
    3. Re-run backtest and log performance differences.
    """
    
    
    
    with open("./configs/base.yaml", "r") as f:
        config = yaml.safe_load(f)

    df = pd.read_csv("./" + config['data']['clean_ES']) 
    #df = load_data(config['data']['clean_ES'])             !!!!! DA SOSTITUIRE

    config_opt = ['use_hurst', 'use_RSI_exit', 'use_take_profit']
    output = []

    for opt in config_opt:
        tmp_config = copy.deepcopy(config)
        tmp_config['ablation'][opt] = False
        strategy = Strategy(cfg=tmp_config)

        res = run(df=df, strategy=strategy)

        cum_factors = []
        cum_factor = 1.0

        for t in res:
            p = t["profit"]
        if p is None:
            cum_factors.append(cum_factor)
            continue
        cum_factor *= (1 + p)
        cum_factors.append(cum_factor)

        metrics = {
            "sharpe_ratio": sharpe_ratio((t["profit"] for t in res)),
            "max_drawdown": max_drawdown(cum_factors),
            "cagr": cagr(cum_factors)
        }
        logging.info("-" * 50)
        logging.info("\nDISABLED feature: \t ", opt)
        out = {
            "disaled_feature": opt,
            "all_trades": res,
            "metrics": metrics
        }
        output.append(out)
        logging.info("-" * 50) 
        logging.info("\n\n- METRICS")
        logging.info("\n sharpe ratio ->", metrics["sharpe_ratio"])
        logging.info("\n max_drawdown ->", metrics["max_drawdown"])
        logging.info("\n cagr ->", metrics["cagr"])
        logging.info("\n")
        logging.info("-" * 50) 
    
    return

if __name__ == '__main__':
    main()