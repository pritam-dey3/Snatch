import gc
import logging
import threading
import time
import traceback as tb
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from driver import get_driver, SystemType
from utils import get_id, start_xvfb, stop_xvfb

SYS = "amd64"
SAVE_DIR = Path("/scrape/html_files/")
GECKO_PATH = Path("/snatch/tor-browser/")
THREAD_FAIL_LIMIT = 20

logging.basicConfig(
    level=logging.INFO,
    filename="scrape.log",
    filemode="w",
    datefmt="%Y-%m-%d %H:%M:%S",
)

THREAD_LOCAL = threading.local()
THREAD_LOCAL.n_failures = 0


class Driver:
    def __init__(self, system: SystemType = "", save_dir: str = ""):
        self.id = uuid.uuid4()
        self.display = start_xvfb()
        self.driver = get_driver(system=system, save_dir=save_dir)
        # self.driver.set_page_load_timeout(15)
        logging.info(f"Created driver {self.id}.")

    def __del__(self):
        self.driver.quit()  # clean up driver when we are cleaned up
        stop_xvfb(self.display)
        logging.info(f"The driver {self.id} has been quitted.")

    @classmethod
    def create_driver(cls, system: SystemType = "", save_dir: str | Path = ""):
        if isinstance(save_dir, Path):
            save_dir = save_dir.as_posix()
        the_driver = getattr(THREAD_LOCAL, "the_driver", None)
        if the_driver is None:
            the_driver = cls(system, save_dir)
            THREAD_LOCAL.the_driver = the_driver
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

        file = SAVE_DIR / f"{url_id}.html"
        with open(file, "w") as f:
            f.write(driver.page_source)
    except Exception as e:
        logging.error(f"Error scraping {url}: {e}\n{tb.format_exc()}")
        n_failures = getattr(THREAD_LOCAL, "n_failures", 0)
        n_failures += 1
        if n_failures > THREAD_FAIL_LIMIT:
            logging.error("Too many failures, exiting thread.")
            raise RuntimeError("Too many failures")
        THREAD_LOCAL.n_failures = n_failures

    end = time.time()
    logging.info(f"processing finished of {url} in {end - start:.2f} seconds.")


def scrape_urls(
    urls: list[str],
    system: str = "",
    html_dir: Path | None = None,
    gecko_path: Path | None = None,
    thread_fail_limit: int | None = None,
    n_threads: int | None = None,
):
    global SYS, SAVE_DIR, GECKO_PATH, THREAD_FAIL_LIMIT
    SYS = system if system else SYS
    SAVE_DIR = html_dir if html_dir else SAVE_DIR
    GECKO_PATH = gecko_path if gecko_path else GECKO_PATH
    THREAD_FAIL_LIMIT = thread_fail_limit if thread_fail_limit else THREAD_FAIL_LIMIT

    logging.info(f"Using {SYS=}, {THREAD_FAIL_LIMIT=}, {SAVE_DIR=}, {GECKO_PATH=}")

    with ThreadPoolExecutor(max_workers=n_threads) as executor:
        futures = [executor.submit(scraper, url) for url in urls]
        for future in futures:
            try:
                future.result()
            except RuntimeError as e:
                logging.error(f"Error: {e}, probably too many failures")
                executor.shutdown(wait=False)


        # Must ensure drivers are quitted before threads are destroyed:
        # del thread_local
        # This should ensure that the __del__ method is run on class Driver:
        gc.collect()
        executor.shutdown()
