# -*- coding: utf-8 -*-
from dotenv import load_dotenv
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env")


def get_env(key: str, default=None) -> str:
    return os.getenv(key, default)


def openai_key() -> str:
    return get_env("OPEN_AI_API_KEY")


def gemini_key() -> str:
    return get_env("GEMINI_API_KEY")


if __name__ == '__main__':
    print(get_env("OPEN_AI_API_KEY"))

SYS_PROMPT = "一个助手，简洁明了的回复，可提供适量建议，不引导用户持续提问"

OLLAMA_MODEL = "qwen3.5:2b"
OPENAI_MODEL = "gpt-5-nano-2025-08-07"
