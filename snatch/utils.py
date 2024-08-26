from hashlib import sha256
from pyvirtualdisplay import Display
import platform


def get_id(url: str) -> str:
    return sha256(url.encode()).hexdigest()


def start_xvfb(**kwargs):
    """Start and return virtual display using XVFB."""
    xvfb_display = Display(visible=False, **kwargs)
    xvfb_display.start()
    return xvfb_display


def stop_xvfb(display: Display):
    """Stop virtual display."""
    if display:
        display.stop()


def platform_info():
    return platform.system().lower(), platform.machine()


def get_user_agent():
    os, machine = platform_info()
    if os == "linux" and machine == "aarch64":
        user_agent = (
            "Mozilla/5.0 (X11; Linux aarch64; rv:90.0) Gecko/20100101 Firefox/90.0"
        )
    else:
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        user_agent += "AppleWebKit/537.36 (KHTML, like Gecko) "
        user_agent += "Chrome/42.0.2311.135 Safari/537.36 Edge/12.246"
    return user_agent
