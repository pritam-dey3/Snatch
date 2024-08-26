import gc
import logging
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor

from selenium.webdriver import Firefox
from selenium.webdriver.common.by import By
from tqdm import tqdm

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


def save_html_file(html: str | None, url: str, config: Config):
    if html is None:
        logging.error(f"Failed to get data from {url}.")
        return

    filename = config.html_dir / f"{get_id(url)}.html"
    with open(filename, "w") as f:
        f.write(html)

    with open(config.completed_urls_file, "a") as f:
        f.write(f"{url}\n")


def scraper(url: str, rel_xpath: str):
    """
    This now scrapes a single URL.
    """

    start = time.time()

    driver = Driver.create_driver()
    logging.info(f"Getting data from: {url}")
    driver.get(url)
    html = driver.find_element(By.XPATH, rel_xpath).get_attribute("outerHTML")

    end = time.time()
    logging.info(f"processing finished of {url} in {end - start:.2f} seconds.")
    return html, url


def scrape_urls(urls: list[str], config: Config):
    n_failures = 0
    keyboard_interrupt = False
    with ThreadPoolExecutor(max_workers=config.n_threads) as executor:
        futures = [
            executor.submit(
                scraper,
                url=url,
                rel_xpath=config.rel_xpath,
            )
            for url in urls
        ]
        for future in tqdm(futures):
            try:
                html, url = future.result()
                save_html_file(html, url, config)
            except KeyboardInterrupt:
                logging.error("Keyboard interrupt")
                keyboard_interrupt = True
                break
            except Exception as e:
                logging.error(f"Error: {e}")
                n_failures += 1
                if n_failures > config.fail_limit:
                    logging.error("Too many failures. Exiting.")
                    break
        # Must ensure drivers are quitted before threads are destroyed:
        # del thread_local
        # This should ensure that the __del__ method is run on class Driver:
        gc.collect()
        executor.shutdown(wait=False)

        if keyboard_interrupt:
            logging.error("Keyboard interrupt. Exiting.")
            raise KeyboardInterrupt
