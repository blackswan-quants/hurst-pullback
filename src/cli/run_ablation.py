import yaml
from src.core.loader import load_data
from src.core.engine import run
from src.strategy.strategy import Strategy
import pandas as pd 
import copy
import logging

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
        logging.info("-" * 50)
        logging.info("\nDISABLED feature: \t ", opt)
        out = {
            "disaled_feature": opt,
            "output": res
        }
        output.append(out)
        logging.info("\n\n- GENERAL INFOs")
        logging.info("\nequity -> ", res["equity"])
        logging.info("\nn_trades -> ", res["n_trades"])
        logging.info("\ntrades -> ", res["trades"])
        logging.info("\n\n- METRICS")
        # metrics QUI
        logging.info("\n")
        logging.info("-" * 50) 
    
    return

if __name__ == '__main__':
    main()