import logging
from typing import Any

from selenium import webdriver

from snatch.utils import platform_info


def set_options(options: dict[str, Any] = {}):
    user_agent = options.get("general.useragent.override", None)

    os, machine = platform_info()
    if not user_agent:
        if os == "linux" and machine == "aarch64":
            user_agent = (
                "Mozilla/5.0 (X11; Linux aarch64; rv:90.0) Gecko/20100101 Firefox/90.0"
            )
        else:
            user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            user_agent += "AppleWebKit/537.36 (KHTML, like Gecko) "
            user_agent += "Chrome/42.0.2311.135 Safari/537.36 Edge/12.246"
        logging.info(f"No user agent provided. Using default: {user_agent}")

    opt = webdriver.FirefoxOptions()
    # opt.set_preference("network.proxy.type", 1)
    # opt.set_preference("network.proxy.socks", "127.0.0.1")
    # opt.set_preference("network.proxy.socks_port", port)
    # opt.set_preference("general.useragent.override", user_agent)
    # opt.set_preference("http.response.timeout", timeout)
    # opt.set_preference("dom.max_script_run_time", script_timeout)
    for key, value in options.items():
        opt.set_preference(key, value)

    return opt


def get_driver(executable_path: str = "", options: dict[str, Any] = {}):
    # port: int = 9050,
    # user_agent: str = "",
    # timeout: int = 15,
    # script_timeout: int = 15,
    os, machine = platform_info()
    if os == "linux" and machine == "aarch64":
        logging.info("Using Raspberry Pi 5.")
        if not executable_path:
            executable_path = "/usr/local/bin/geckodriver"
        logging.info(f"Using geckodriver at {executable_path}.")
        sv = webdriver.FirefoxService(executable_path=executable_path)
        return webdriver.Firefox(
            options=set_options(
                options=options,
            ),
            service=sv,
        )
    else:
        logging.info("Using amd64.")
        return webdriver.Firefox(
            options=set_options(
                options=options,
            )
        )
