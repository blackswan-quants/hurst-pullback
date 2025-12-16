# hurst-pullback

Reproducible Python implementation of the Hurst-Regime Pullback Strategy for index futures (ES, NQ, EMD, YM) — QuantConnect-ready research framework.

## Development

Quick setup using [UV](https://docs.astral.sh/uv/getting-started/installation/), make sure you have installed it before doing any of the following steps:

1. Create the virtual environment and install dependencies
```sh
uv sync
```
This creates `.venv`, installs required packages and ensures the correct Python version.

2. Activate the environment

- PowerShell (Windows)
```powershell
.\.venv\Scripts\Activate.ps1
```
- Command Prompt (Windows)
```cmd
.\.venv\Scripts\activate.bat
```
- macOS / Linux
```sh
source .venv/bin/activate
```

## Dependencies 

Python dependencies and tools are managed with UV. This is how to install a library (UV will add this to the dependencies list automatically).

```sh
uv add pandas  # code dependencies
uv add --dev black # development tools
```


## Configs

All flags and input parameters are initialized in the file base.yaml. You need to import the file, this is an example:

```sh
import yaml

yaml_path = Path().resolve().parent / "configs" / "base.yaml"
with open(yaml_path, "r") as f:
    config = yaml.safe_load(f)
```
Then you can use initialized variables using this syntax:
```sh
config["data"]["clean_NQ"]  # this line select the path of "clean_NQ" which is part of the subset data in the base file
```

## Fee Structure

The backtesting system incorporates realistic trading costs through two main components configured in `configs/base.yaml`:

- `commission_per_contract`: Set at **$2.50** per round turn (entry + exit), this parameter reflects typical costs including broker commissions, exchange fees, clearing fees, and regulatory charges for futures (ES, NQ, YM, EMD).

- `slippage_per_contract`: Set at **$15.00** per round turn, this accounts for the difference between expected and actual execution prices. This represents approximately 2-3 ticks of slippage per side across the instruments traded, capturing realistic market impact under normal liquidity conditions. Slippage varies by instrument tick value: ES ($12.50/tick), NQ ($5/tick), YM ($5/tick), and EMD ($10/tick).
