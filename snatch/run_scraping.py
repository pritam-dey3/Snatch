from pathlib import Path

from snatch.scrape import scrape_urls
from snatch.utils import get_id
from snatch.config import Config


def get_remaining_urls(url_path: Path, html_dir: Path):
    with open(url_path, "r") as f:
        urls = [ln.strip() for ln in f.readlines()]

    html_dir.mkdir(exist_ok=True, parents=True)
    existing_ids = []
    for p in html_dir.iterdir():
        existing_ids.append(p.stem)

    return [url for url in urls if get_id(url) not in existing_ids]


def run_scraping(config: Config):
    urls_to_scrape = get_remaining_urls(config.urls_file, config.html_dir)
    while len(urls_to_scrape) > 0:
        print(f"Scraping {len(urls_to_scrape)} URLs.")
        scrape_urls(urls_to_scrape, config)
        urls_to_scrape = get_remaining_urls(config.urls_file, config.html_dir)
