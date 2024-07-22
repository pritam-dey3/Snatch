from pathlib import Path

from scrape import scrape_urls
from utils import get_id

url_path = "/scrape/urls.txt"
save_dir = Path("/scrape/save_dir/")
save_dir.mkdir(exist_ok=True, parents=True)


def get_urls():
    with open(url_path, "r") as f:
        urls = [ln.strip() for ln in f.readlines()]

    existing_ids = []
    for p in save_dir.iterdir():
        existing_ids.append(p.stem)

    return [url for url in urls if get_id(url) not in existing_ids]


urls_to_scrape = get_urls()
while len(urls_to_scrape) > 0:
    print(f"Scraping {len(urls_to_scrape)} URLs.")
    scrape_urls(urls_to_scrape, system="debian")
    urls_to_scrape = get_urls()
