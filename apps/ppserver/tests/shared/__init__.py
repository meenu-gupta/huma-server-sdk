from pathlib import Path

APPS_CONFIG_PATH = Path(__file__).with_name("config.test.yaml")
# NOTE: keep str() here, otherwise migrations won't be found
APPS_MIGRATIONS = str(Path(__file__).parent.joinpath("../migrations"))
