import gc
import logging
import threading
import time
import traceback as tb
import uuid
from multiprocessing.pool import ThreadPool
from pathlib import Path

from tbselenium.tbdriver import TorBrowserDriver
from tbselenium.utils import start_xvfb, stop_xvfb

from utils import get_id


html_dir = Path("/scrape/html_files/")
tor_browser_path = "/snatch/tor-browser/"
fail_threshold = 20


logging.basicConfig(
    level=logging.INFO,
    filename="scrape.log",
    filemode="w",
    datefmt="%Y-%m-%d %H:%M:%S",
)


html_dir.mkdir(exist_ok=True)

thread_local = threading.local()
thread_local.n_failures = 0


class Driver:
    def __init__(self):
        self.id = uuid.uuid4()
        self.display = start_xvfb()
        self.driver = TorBrowserDriver(tor_browser_path)
        self.driver.set_page_load_timeout(15)
        logging.info(f"Created driver {self.id}.")

    def __del__(self):
        self.driver.quit()  # clean up driver when we are cleaned up
        stop_xvfb(self.display)
        logging.info(f"The driver {self.id} has been quitted.")

    @classmethod
    def create_driver(cls):
        the_driver = getattr(thread_local, "the_driver", None)
        if the_driver is None:
            the_driver = cls()
            thread_local.the_driver = the_driver
        driver = the_driver.driver
        the_driver = None
        return driver


def scraper(url):
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
        with open(file, "w") as f:
            f.write(driver.page_source)
    except Exception as e:
        logging.error(f"Error scraping {url}: {e}\n{tb.format_exc()}")
        n_failures = getattr(thread_local, "n_failures", 0)
        n_failures += 1
        if n_failures > fail_threshold:
            raise RuntimeError("Too many failures")
        thread_local.n_failures = n_failures

    end = time.time()
    logging.info(f"processing finished of {url} in {end - start:.2f} seconds.")


def scrape_urls(urls: list[str]):
    with ThreadPool() as pool:
        try:
            pool.map(scraper, urls)
        except RuntimeError as e:
            logging.error(f"Error: {e}, probably too many failures")
        except AttributeError as e:
            logging.error(f"Error: {e}, probably too many failures")

        # Must ensure drivers are quitted before threads are destroyed:
        # del thread_local
        # This should ensure that the __del__ method is run on class Driver:
        gc.collect()
        pool.close()
        pool.join()
