import yaml 
import logging 
import sys
from pathlib import Path
import pandas as pd

# Handle both module and direct execution
try:
    from ..strategy.strategy import Strategy
    from ..core.engine import run
except ImportError:
    # If running directly, add parent directory to path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from src.strategy.strategy import Strategy
    from src.core.engine import run

def main() -> None:
    """
    Main entrypoint for executing a single backtest.
    Steps:
    1. Load YAML configuration.
    2. Load and clean data.
    3. Initialize Strategy instance.
    4. Run backtest through engine.
    5. Print resulting equity and metrics.
    """
    # Get project root directory
    project_root = Path(__file__).parent.parent.parent
    
    config_path = project_root / "configs" / "base.yaml"
    with open(config_path, 'r') as file:
        data = yaml.safe_load(file)
    
    ###### logging setup ########
    logger_config = data.get('logger', {})
    DEFAULT_LEVEL = 'INFO'
    DEFAULT_FALLBACK = logging.DEBUG # What to set if the level is invalid
    LOGGER_MAP = {
        'engine': 'engine_level',
        'strategy_entry': 'strategy_entry_level',
        'strategy_exit': 'strategy_exit_level',
        'indicators': 'indicators_level',
        'ablation': 'ablation_level',
    }

    print("\n--- Starting Logger Configuration ---") # Used for visibility during runtime

    for logger_name, config_key in LOGGER_MAP.items():
        
        level_str = logger_config.get(config_key, DEFAULT_LEVEL)
        
        logger_instance = logging.getLogger(logger_name)
        try:
            level_enum = getattr(logging, level_str.upper())
            logger_instance.setLevel(level_enum)
        
            logging.info(f"Logger '{logger_name}' set to level: {level_str.upper()}")
            
        except AttributeError:
            logger_instance.setLevel(DEFAULT_FALLBACK)
            logging.warning(f"Level '{level_str}' in YAML for '{config_key}' is not valid. Falling back to {DEFAULT_FALLBACK.name}.")

    print("--- Logger Configuration Complete ---\n")

    #### end logging setup ####

    #### dataframe loading ####
    data_path = project_root / "data" / "clean" / "NQ_clean.csv"
    try:
        df = pd.read_csv(data_path)
        # Log success
        logging.info('Successfully loaded the dataframe.')

    except FileNotFoundError:
        logging.error(f'File not found: {data_path}. Cannot load the dataframe.')
        return
    except Exception as e:
        logging.error(f'An unexpected error occurred during file loading: {e}')
        return
    
    #### backtest running ####
    strategy = Strategy(data)
    logging.info(strategy.get_cfg())
    all_trades = run(df, strategy)
    print(f"Completed {len(all_trades)} trades")
    print(all_trades)

if __name__ == "__main__":
    main()

