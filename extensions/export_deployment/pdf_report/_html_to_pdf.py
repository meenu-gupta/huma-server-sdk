import base64
from contextlib import contextmanager
from pathlib import Path
from typing import Union

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.print_page_options import PrintOptions


def html_to_pdf(path: Union[str, Path]):
    with _launch_headless_chrome() as chrome:
        chrome.get(f"file:///{path}")
        options = PrintOptions()
        options.background = True
        options.margin_top = options.margin_bottom = 0
        options.margin_right = options.margin_left = 0
        result = chrome.print_page(options)
        return base64.b64decode(result)


@contextmanager
def _launch_headless_chrome():
    webdriver_options = Options()
    webdriver_options.add_argument("--headless")
    webdriver_options.add_argument("--disable-gpu")
    webdriver_options.add_argument("--no-sandbox")
    webdriver_options.add_argument("--disable-dev-shm-usage")

    chrome_driver_path = Path(__file__).parent.joinpath("utils/chromedriver")
    driver = webdriver.Chrome(chrome_driver_path, options=webdriver_options)
    try:
        yield driver
    finally:
        driver.quit()
