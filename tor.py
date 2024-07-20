from tbselenium.tbdriver import TorBrowserDriver
from pathlib import Path
from utils import get_id
import logging

logging.basicConfig(level=logging.DEBUG)

def tor_load_n_save(driver: TorBrowserDriver, url:str, save_dir: Path):
    try:
        driver.get(url)
        with open(save_dir / f"{get_id(url)}.html", 'w', encoding='utf-8') as file:
            file.write(driver.page_source)
    except Exception as e:
        logging.error(f"Error: {e} on {url}")
