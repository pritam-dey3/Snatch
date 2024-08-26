import gc
import logging
import threading
import time
import traceback as tb
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from selenium.webdriver import Firefox
from selenium.webdriver.common.by import By

from snatch.config import Config
from snatch.driver import get_driver
from snatch.utils import get_id, start_xvfb, stop_xvfb

logging.basicConfig(
    level=logging.INFO,
    filename="scrape.log",
    filemode="w",
    datefmt="%Y-%m-%d %H:%M:%S",
)

THREAD_LOCAL = threading.local()
THREAD_LOCAL.n_failures = 0


class Driver:
    def __init__(self):
        self.id = uuid.uuid4()
        self.display = start_xvfb()
        self.driver = get_driver()
        # self.driver.set_page_load_timeout(15)
        logging.info(f"Created driver {self.id}.")

    def __del__(self):
        self.driver.quit()  # clean up driver when we are cleaned up
        stop_xvfb(self.display)
        logging.info(f"The driver {self.id} has quit.")

    @classmethod
    def create_driver(cls) -> Firefox:
        the_driver = getattr(THREAD_LOCAL, "the_driver", None)
        if the_driver is None:
            the_driver = cls()
            THREAD_LOCAL.the_driver = the_driver
        driver = the_driver.driver
        the_driver = None
        return driver


def scraper(url: str, html_dir: Path, thread_fail_limit: int, rel_xpath: str):
    """
    This now scrapes a single URL.
    """

    start = time.time()

    try:
        driver = Driver.create_driver()
        logging.info(f"Getting data from: {url}")
        driver.get(url)
        url_id = get_id(url)

        file = html_dir / f"{url_id}.html"
        html = driver.find_element(By.XPATH, rel_xpath).get_attribute("outerHTML")
        if html is None:
            logging.error(f"Could not find HTML for {url}")
            return
        with open(file, "w") as f:
            f.write(html)
    except Exception as e:
        logging.error(f"Error scraping {url}: {e}\n{tb.format_exc()}")
        n_failures = getattr(THREAD_LOCAL, "n_failures", 0)
        n_failures += 1
        if n_failures > thread_fail_limit:
            logging.error("Too many failures, exiting thread.")
            raise RuntimeError("Too many failures")
        THREAD_LOCAL.n_failures = n_failures

    end = time.time()
    logging.info(f"processing finished of {url} in {end - start:.2f} seconds.")


def scrape_urls(urls: list[str], config: Config):
    with ThreadPoolExecutor(max_workers=config.n_threads) as executor:
        futures = [
            executor.submit(
                scraper,
                url=url,
                html_dir=config.html_dir,
                thread_fail_limit=config.thread_fail_limit,
                rel_xpath=config.rel_xpath,
            )
            for url in urls
        ]
        for future in futures:
            try:
                future.result()
            except RuntimeError as e:
                logging.error(f"Error: {e}, probably too many failures")
                executor.shutdown(wait=False)
            except KeyboardInterrupt:
                logging.error("Keyboard interrupt")
                executor.shutdown(wait=False)
                raise KeyboardInterrupt
        # Must ensure drivers are quitted before threads are destroyed:
        # del thread_local
        # This should ensure that the __del__ method is run on class Driver:
        gc.collect()
        executor.shutdown()
