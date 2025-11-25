import yaml 
import logging 
import sys
from pathlib import Path
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

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

    strategy = Strategy(data)
    logging.info(strategy.get_cfg())
    all_trades = run(df, strategy)
    print(f"Completed {len(all_trades)} trades")
    print(all_trades)

if __name__ == "__main__":
    main()

