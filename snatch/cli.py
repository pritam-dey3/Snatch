from cyclopts import App
from snatch.config import Config
from rich import print
from snatch.run_scraping import run_scraping

app = App()


@app.command()
def test():
    config = Config().model_dump(by_alias=True)
    print(config)

@app.command()
def scrape():
    config = Config()
    print(config)
    run_scraping(config)


if __name__ == "__main__":
    app()
