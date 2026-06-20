from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

from pipeline.config import REPO_ROOT

SUPPORTED_PROVIDERS = ("openai", "anthropic")


@dataclass(frozen=True)
class Settings:
    openai_api_key: str | None
    anthropic_api_key: str | None
    default_provider: str
    openai_model: str
    anthropic_model: str
    request_timeout_seconds: float
    max_retries: int

    @property
    def has_openai(self) -> bool:
        return bool(self.openai_api_key)

    @property
    def has_anthropic(self) -> bool:
        return bool(self.anthropic_api_key)

    def api_key_for_provider(self, provider: str) -> str:
        normalized = provider.strip().lower()
        if normalized not in SUPPORTED_PROVIDERS:
            raise ValueError(
                f"Unsupported provider '{provider}'. Expected one of: {', '.join(SUPPORTED_PROVIDERS)}"
            )

        if normalized == "openai":
            if not self.openai_api_key:
                raise RuntimeError(
                    "OPENAI_API_KEY is not set. Add it to your environment or .env file."
                )
            return self.openai_api_key

        if not self.anthropic_api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY is not set. Add it to your environment or .env file."
            )
        return self.anthropic_api_key

    def model_for_provider(self, provider: str) -> str:
        normalized = provider.strip().lower()
        if normalized == "openai":
            return self.openai_model
        if normalized == "anthropic":
            return self.anthropic_model
        raise ValueError(f"Unsupported provider '{provider}'.")


def load_env(repo_root: Path = REPO_ROOT) -> None:
    env_path = repo_root / ".env"
    if env_path.exists():
        load_dotenv(env_path, override=False)


def _read_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    return float(raw)


def _read_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    return int(raw)


def load_settings(repo_root: Path = REPO_ROOT) -> Settings:
    load_env(repo_root=repo_root)

    default_provider = os.getenv("DEFAULT_PROVIDER", "anthropic").strip().lower()
    if default_provider not in SUPPORTED_PROVIDERS:
        raise ValueError(
            f"DEFAULT_PROVIDER must be one of {SUPPORTED_PROVIDERS}, got '{default_provider}'."
        )

    return Settings(
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        default_provider=default_provider,
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4o"),
        anthropic_model=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6"),
        request_timeout_seconds=_read_float("REQUEST_TIMEOUT_SECONDS", 120.0),
        max_retries=_read_int("MAX_RETRIES", 2),
    )


def provider_status(settings: Settings) -> dict[str, bool]:
    return {
        "openai": settings.has_openai,
        "anthropic": settings.has_anthropic,
    }
