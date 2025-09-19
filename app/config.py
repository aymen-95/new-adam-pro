from __future__ import annotations
from functools import lru_cache
from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = Field(default="Smart Core Adam Pro", alias="APP_NAME")
    environment: str = Field(default="development", alias="ENVIRONMENT")
    memory_path: str = Field(default="data/memory.json", alias="MEMORY_PATH")
    enable_think_loop: bool = Field(default=True, alias="ENABLE_THINK_LOOP")
    think_interval_seconds: float = Field(default=7.0, alias="THINK_INTERVAL_SECONDS")
    active_models: List[str] = Field(default_factory=lambda: ["gpt", "deepseek", "gemini", "copilot"], alias="ACTIVE_MODELS")
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }

    @field_validator("active_models", mode="before")
    @classmethod
    def _parse_active_models(cls, v):
        """Robust parsing for ACTIVE_MODELS from .env.

        Supports:
        - empty or missing -> default list
        - comma-separated e.g. "gpt,gemini"
        - JSON array e.g. ["gpt","gemini"]
        """
        if v is None:
            return ["gpt", "deepseek", "gemini", "copilot"]
        if isinstance(v, list):
            return v
        s = str(v).strip()
        if not s:
            return ["gpt", "deepseek", "gemini", "copilot"]
        if s.startswith("["):
            try:
                import json
                arr = json.loads(s)
                if isinstance(arr, list):
                    return [str(x).strip() for x in arr if str(x).strip()]
            except Exception:
                # fall through to comma parser
                pass
        return [part.strip() for part in s.split(",") if part.strip()]


@lru_cache()
def get_settings() -> Settings:
    return Settings()
