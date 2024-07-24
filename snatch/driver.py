import logging
from typing import Literal
import uuid
from pathlib import Path
import threading

from selenium.webdriver import Firefox, FirefoxOptions, FirefoxService
from snatch.utils import start_xvfb, stop_xvfb

SystemType = Literal["", "rpi5", "debian"]


def set_options(
    system: SystemType = "",
    port: int = 9050,
    user_agent: str = "",
    save_dir: str = "",
):
    if not user_agent:
        if system == "rpi5":
            user_agent = (
                "Mozilla/5.0 (X11; Linux aarch64; rv:90.0) Gecko/20100101 Firefox/90.0"
            )
        elif system == "debian":
            user_agent = (
                "Mozilla/5.0 (X11; Linux x86_64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/91.0.4472.124 Safari/537.36"
            )
        else:
            user_agent = (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/91.0.4472.124 Safari/537.36"
            )
    logging.info(f"Using user agent: {user_agent}")

    opt = FirefoxOptions()
    opt.set_preference("network.proxy.type", 1)
    opt.set_preference("network.proxy.socks", "127.0.0.1")
    opt.set_preference("network.proxy.socks_port", port)
    opt.set_preference("general.useragent.override", user_agent)

    # Enable JavaScript
    opt.set_preference("javascript.enabled", True)

    # Other preferences to mimic real user behavior
    opt.set_preference("dom.webdriver.enabled", False)
    opt.set_preference("media.peerconnection.enabled", False)
    opt.set_preference("useAutomationExtension", False)
    opt.set_preference(
        "permissions.default.image", 2
    )  # This can disable images for faster scraping, set to 1 to enable images
    opt.set_preference(
        "permissions.default.stylesheet", 2
    )  # This can disable CSS for faster scraping, set to 1 to enable CSS
    opt.set_preference("permissions.default.script", 1)  # Ensure scripts are allowed

    # Download options
    opt.set_preference(
        "browser.download.folderList", 2
    )  # Use custom download directory
    opt.set_preference("browser.download.dir", save_dir)
    opt.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/pdf")
    # opt.set_preference("pdfjs.disabled", True)  # Disable Firefox's built-in PDF viewer
    return opt


class Driver:
    def __init__(
        self, system: SystemType, executable_path: str, save_dir: str, timeout: int
    ):
        self.id = uuid.uuid4()
        self.display = start_xvfb()
        self.driver = get_driver(
            system=system, executable_path=executable_path, save_dir=save_dir, port=9050
        )
        self.driver.set_page_load_timeout(timeout)
        logging.info(f"Created driver {self.id}.")

    def __del__(self):
        self.driver.quit()  # clean up driver when we are cleaned up
        stop_xvfb(self.display)
        logging.info(f"The driver {self.id} has been quitted.")

    @classmethod
    def create(
        cls,
        system: SystemType,
        thread_local: threading.local,
        executable_path: str | Path,
        save_dir: str | Path,
        timeout: int,
    ) -> Firefox:
        if isinstance(save_dir, Path):
            save_dir = save_dir.as_posix()
        if isinstance(executable_path, Path):
            executable_path = executable_path.as_posix()
        the_driver = getattr(thread_local, "the_driver", None)
        if the_driver is None:
            the_driver = cls(
                system=system,
                executable_path=executable_path,
                save_dir=save_dir,
                timeout=timeout,
            )
            thread_local.the_driver = the_driver
        driver = the_driver.driver
        the_driver = None
        return driver



def get_driver(
    system: SystemType = "",
    executable_path: str = "",
    port: int = 9050,
    user_agent: str = "",
    save_dir: str = "",
):
    if system == "rpi5":
        logging.info("Using Raspberry Pi 5.")
        if not executable_path:
            executable_path = "/usr/local/bin/geckodriver"
        logging.info(f"Using geckodriver at {executable_path}.")
        sv = FirefoxService(executable_path=executable_path)
        return Firefox(
            options=set_options(
                system,
                port=port,
                user_agent=user_agent,
                save_dir=save_dir,
            ),
            service=sv,
        )
    else:
        logging.info("Using amd64.")
        return Firefox(
            options=set_options(
                system,
                port=port,
                user_agent=user_agent,
                save_dir=save_dir,
            )
        )
