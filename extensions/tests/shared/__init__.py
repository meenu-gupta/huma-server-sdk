from pathlib import Path

EXTENSIONS_CONFIG_PATH = Path(__file__).with_name("config.test.yaml")
RATE_LIMITER_CONFIG_PATH = Path(__file__).with_name("config.rate-limiter.test.yaml")
# NOTE: keep str() here, otherwise migrations won't be found
EXTENSIONS_MIGRATIONS = str(Path(__file__).parent.joinpath("../migrations"))
