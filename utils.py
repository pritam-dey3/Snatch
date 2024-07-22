from hashlib import sha256
from pyvirtualdisplay import Display


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
