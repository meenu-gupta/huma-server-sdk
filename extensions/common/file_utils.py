import os
from contextlib import contextmanager
from pathlib import Path
from typing import Union


@contextmanager
def use_temp_file(path: Union[str, Path]):
    open(path, "w").close()
    try:
        yield
    finally:
        os.remove(path)
