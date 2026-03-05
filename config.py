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

SYS_PROMPT = "一个助手，简洁明了的回复，可提供适量建议，但是不反问用户问题"
OLLAMA_MODEL = "qwen3.5:2b"
