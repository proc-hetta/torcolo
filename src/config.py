import os
import configparser
from dataclasses import dataclass


@dataclass
class Config:
    token: str
    db_url: str
    log_level: str
    def __init__(self):
        config = configparser.ConfigParser()
        config.read(os.getenv("TORCOLO_CONFIG_PATH", "config.ini"))
        self.token = config["Core"]["Token"]
        self.db_url = config["Core"]["DbUrl"]
        self.log_level = config["Core"]["LogLevel"]


config = Config()
