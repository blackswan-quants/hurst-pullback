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
