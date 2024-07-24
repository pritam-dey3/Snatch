import gc
import logging
import threading
import time
import traceback as tb
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from subprocess import PIPE, call
from typing import Callable, Iterable

from selenium.webdriver import Firefox
from tqdm import tqdm

from snatch.driver import Driver, SystemType

# check if tor service is running, if not start tor
status = call(["service", "tor", "status"], stdout=PIPE)
if status == 4:
    call(["service", "tor", "start"], stdout=PIPE)
elif status in [1, 2, 3]:
    print(f"Tor service is not available. `service tor status` returned: {status}.")

# TODO: check if tor is running on port 9050


logging.basicConfig(
    level=logging.INFO,
    filename="scrape.log",
    filemode="w",
    datefmt="%Y-%m-%d %H:%M:%S",
)

THREAD_LOCAL = threading.local()
THREAD_LOCAL.n_failures = 0


def scraper[T](
    url: str,
    page_handler: Callable[[Firefox], T],
    executable_path: Path,
    save_dir: str,
    system: SystemType,
    thread_fail_limit: int,
    timeout: int,
) -> T | None:
    """
    This now scrapes a single URL.
    """

    start = time.time()

    try:
        driver = Driver.create(
            system=system,
            thread_local=THREAD_LOCAL,
            executable_path=executable_path,
            save_dir=save_dir,
            timeout=timeout,
        )
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
    urls: Iterable[str],
    page_handler: Callable[[Firefox], T],
    executable_path: Path,
    system: SystemType = "",
    save_dir="",
    thread_fail_limit: int = 20,
    timeout: int = 180,
    n_threads: int | None = None,
) -> list[T]:
    logging.info(f"Using {system=}, {executable_path=}, {thread_fail_limit=}")

    results: list[T] = []
    with ThreadPoolExecutor(max_workers=n_threads) as executor:
        futures = [
            executor.submit(
                scraper,
                url=url,
                page_handler=page_handler,
                executable_path=executable_path,
                save_dir=save_dir,
                system=system,
                thread_fail_limit=thread_fail_limit,
                timeout=timeout,
            )
            for url in urls
        ]
        for future in tqdm(futures):
            try:
                res = future.result()
                if res is not None:
                    results.append(res)
            except RuntimeError as e:
                logging.error(f"Error: {e}, probably too many failures")
                break
            except KeyboardInterrupt:
                logging.error("KeyboardInterrupt, exiting.")
                executor.shutdown()
                raise KeyboardInterrupt("KeyboardInterrupt")

    # make sure the threads are all destroyed
    del THREAD_LOCAL.the_driver
    gc.collect()
    return results
