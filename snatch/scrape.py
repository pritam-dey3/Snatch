import gc
import logging
import threading
import time
import traceback as tb
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from subprocess import PIPE, call
from typing import Callable

from snatch.driver import SystemType, get_driver
from selenium.webdriver import Firefox
from snatch.utils import start_xvfb, stop_xvfb

# check if tor service is running, if not start tor
status = call(["service", "tor", "status"], stdout=PIPE)
if status == 4:
    call(["service", "tor", "start"], stdout=PIPE)
elif status in [1, 2, 3]:
    print(f"Tor service is not available. `service tor status` returned: {status}.")


logging.basicConfig(
    level=logging.INFO,
    filename="scrape.log",
    filemode="w",
    datefmt="%Y-%m-%d %H:%M:%S",
)

THREAD_LOCAL = threading.local()
THREAD_LOCAL.n_failures = 0


class Driver:
    def __init__(self, system: SystemType, gecko_path: str):
        self.id = uuid.uuid4()
        self.display = start_xvfb()
        self.driver = get_driver(system=system, executable_path=gecko_path)
        # self.driver.set_page_load_timeout(15)
        logging.info(f"Created driver {self.id}.")

    def __del__(self):
        self.driver.quit()  # clean up driver when we are cleaned up
        stop_xvfb(self.display)
        logging.info(f"The driver {self.id} has been quitted.")

    @classmethod
    def create_driver(cls, system: SystemType, gecko_path: str | Path):
        if isinstance(gecko_path, Path):
            gecko_path = gecko_path.as_posix()
        the_driver = getattr(THREAD_LOCAL, "the_driver", None)
        if the_driver is None:
            the_driver = cls(system, gecko_path)
            THREAD_LOCAL.the_driver = the_driver
        driver = the_driver.driver
        the_driver = None
        return driver


def scraper[T](
    url: str,
    page_handler: Callable[[Firefox], T],
    gecko_path: Path,
    system: SystemType,
    thread_fail_limit: int,
) -> T | None:
    """
    This now scrapes a single URL.
    """

    start = time.time()

    try:
        driver = Driver.create_driver(system, gecko_path)
        logging.info(f"Getting data from: {url}")
        driver.get(url)
        res: T = page_handler(driver)

        end = time.time()
        logging.info(f"processing finished of {url} in {end - start:.2f} seconds.")
        return res
    except Exception as e:
        logging.error(f"Error scraping {url}: {e}\n{tb.format_exc()}")
        n_failures = getattr(THREAD_LOCAL, "n_failures", 0)
        n_failures += 1
        if n_failures > thread_fail_limit:
            logging.error("Too many failures, exiting thread.")
            raise RuntimeError("Too many failures")
        THREAD_LOCAL.n_failures = n_failures


def scrape_urls[T](
    urls: list[str],
    system: SystemType,
    page_handler: Callable[[Firefox], T],
    gecko_path: Path,
    thread_fail_limit: int,
    n_threads: int | None = None,
) -> list[T]:
    logging.info(f"Using {system=}, {gecko_path=}, {thread_fail_limit=}")

    results: list[T] = []
    with ThreadPoolExecutor(max_workers=n_threads) as executor:
        futures = [
            executor.submit(
                scraper, url, page_handler, gecko_path, system, thread_fail_limit
            )
            for url in urls
        ]
        for future in futures:
            try:
                res = future.result()
                if res is not None:
                    results.append(res)
            except RuntimeError as e:
                logging.error(f"Error: {e}, probably too many failures")
                break

    # make sure the threads are all destroyed
    del THREAD_LOCAL.the_driver
    gc.collect()
    return results
