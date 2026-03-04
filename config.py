# -*- coding: utf-8 -*-

from dotenv import load_dotenv
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env")


def get_env(key: str, default=None) -> str:
    return os.getenv(key, default)


if __name__ == '__main__':
    print(get_env("OPEN_AI_API_KEY"))
