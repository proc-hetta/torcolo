import os
import configparser
from dataclasses import dataclass
from typing import Optional
from packaging.version import Version


VERSION = Version("1.0.1")


@dataclass
class Config:
    token: str
    db_url: str
    log_level: str
    default_limit: int
    default_healthbar: Optional[int]

    def __init__(self):
        config = configparser.ConfigParser()
        config.read(os.getenv("TORCOLO_CONFIG_PATH", "config.ini"))
        self.token = config["Core"]["Token"]
        self.db_url = config["Core"]["DbUrl"]
        self.log_level = config["Core"]["LogLevel"]
        self.default_limit = config["Core"]["DefaultLimit"]
        self.default_healthbar = config["Core"].get("DefaultHealthbar")
        self.alembic_path = config["Migration"]["AlembicPath"]


config = Config()
