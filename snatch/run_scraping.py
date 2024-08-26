from pathlib import Path

from snatch.scrape import scrape_urls
from snatch.utils import get_id
from snatch.config import Config


def get_remaining_urls(url_path: Path, completed_urls_file: Path):
    with open(url_path, "r") as f:
        urls = [ln.strip() for ln in f.readlines()]

    if completed_urls_file.exists():
        with open(completed_urls_file, "r") as f:
            existing_ids = [get_id(ln.strip()) for ln in f.readlines()]
    else:
        existing_ids = []
        completed_urls_file.touch()

    return [url for url in urls if get_id(url) not in existing_ids]


def run_scraping(config: Config):
    urls_to_scrape = get_remaining_urls(config.urls_file, config.completed_urls_file)
    while len(urls_to_scrape) > 0:
        print(f"Scraping {len(urls_to_scrape)} URLs.")
        scrape_urls(urls_to_scrape, config)
        urls_to_scrape = get_remaining_urls(config.urls_file, config.completed_urls_file)
