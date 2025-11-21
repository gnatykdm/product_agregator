from dotenv import load_dotenv
from pydantic import HttpUrl

import os
from pydantic_settings import BaseSettings

load_dotenv()

class Config(BaseSettings):
    AMAZON_URL: HttpUrl = os.getenv("AMAZON_URL")
    EBAY_URL: HttpUrl = os.getenv("EBAY_URL")
    class Config:
        env_file = ".env"

config = Config()