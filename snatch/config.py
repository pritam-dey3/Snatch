from typing import Type, Annotated

from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    YamlConfigSettingsSource,
)
from pydantic import Field, BaseModel
from snatch.utils import get_user_agent
from pathlib import Path


class DriverConfig(BaseModel):
    network_proxy_type: Annotated[int, Field(..., alias="network.proxy.type")] = 1
    network_proxy_socks: Annotated[str, Field(..., alias="network.proxy.socks")] = "127.0.0.1"
    network_proxy_socks_port: Annotated[int, Field(..., alias="network.proxy.socks_port")] = 9050
    general_useragent_override: Annotated[str, Field(..., alias="general.useragent.override")] = get_user_agent()
    http_response_timeout: Annotated[int, Field(..., alias="http.response.timeout")] = 30
    dom_max_script_run_time: Annotated[int, Field(..., alias="dom.max_script_run_time")] = 30


class Config(BaseSettings, cli_parse_args=False):
    urls_file: Path = Path("urls.txt")
    html_dir: Path = Path("html_files/")
    rel_xpath: str = "//body"
    n_threads: int | None = None
    thread_fail_limit: int = 20
    driver: DriverConfig = DriverConfig()


    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (YamlConfigSettingsSource(settings_cls, yaml_file="config.yaml"),)
