import sys
from dataclasses import dataclass


@dataclass
class ProgressBar:
    """
    Utility to show progress of current loop.
    Usage:
        progress_bar = ProgressBar(total=500)
        for index, item in enumerate(items, 1):
            progress_bar.show(current=index)
            process_your_item(item)
            ...
    """

    total: int = 0
    _last_reported_percentage = None

    def show(self, current: int):
        current_percentage = int(current * 100 / self.total)
        if (
            self._last_reported_percentage != current_percentage
            or current == self.total
        ):
            left = 100 - current_percentage
            msg = f"[{'#' * current_percentage}{'-' * left}]{current_percentage}%"
            sys.stdout.write(f"\r{msg}")
        self._last_reported_percentage = current_percentage
