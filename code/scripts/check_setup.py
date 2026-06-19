#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path

CODE_ROOT = Path(__file__).resolve().parents[1]
if str(CODE_ROOT) not in sys.path:
    sys.path.insert(0, str(CODE_ROOT))

from pipeline.config import REPO_ROOT  # noqa: E402
from pipeline.settings import load_settings, provider_status  # noqa: E402

REQUIRED_PACKAGES = (
    ("openai", "openai"),
    ("anthropic", "anthropic"),
    ("dotenv", "python-dotenv"),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify Python dependencies and API key configuration."
    )
    parser.add_argument(
        "--provider",
        choices=("openai", "anthropic"),
        help="Require that this provider's API key is configured.",
    )
    return parser.parse_args()


def check_python_version() -> list[str]:
    if sys.version_info < (3, 10):
        return [f"Python 3.10+ required; found {sys.version.split()[0]}."]
    return []


def check_packages() -> tuple[list[str], list[str]]:
    errors: list[str] = []
    notes: list[str] = []

    for module_name, package_name in REQUIRED_PACKAGES:
        try:
            importlib.import_module(module_name)
            notes.append(f"Installed: {package_name}")
        except ImportError:
            errors.append(
                f"Missing package '{package_name}'. Run: pip install -r code/requirements.txt"
            )

    return errors, notes


def check_env_file() -> list[str]:
    env_path = REPO_ROOT / ".env"
    if env_path.exists():
        return [f"Found local env file: {env_path}"]
    return [
        "No .env file found at repo root. You can copy .env.example to .env or export keys in your shell."
    ]


def check_api_keys(required_provider: str | None) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    notes: list[str] = []

    try:
        settings = load_settings()
    except ValueError as exc:
        return [str(exc)], notes

    status = provider_status(settings)
    notes.append(f"Default provider: {settings.default_provider}")
    notes.append(f"OpenAI key configured: {status['openai']}")
    notes.append(f"Anthropic key configured: {status['anthropic']}")
    notes.append(f"OpenAI model: {settings.openai_model}")
    notes.append(f"Anthropic model: {settings.anthropic_model}")

    provider_to_check = required_provider or settings.default_provider
    if not status[provider_to_check]:
        errors.append(
            f"{provider_to_check.upper()} API key is not set. "
            f"Add it to .env or export {provider_to_check.upper()}_API_KEY."
        )

    return errors, notes


def main() -> int:
    args = parse_args()
    errors: list[str] = []
    notes: list[str] = []

    errors.extend(check_python_version())
    package_errors, package_notes = check_packages()
    errors.extend(package_errors)
    notes.extend(package_notes)
    notes.extend(check_env_file())
    key_errors, key_notes = check_api_keys(args.provider)
    errors.extend(key_errors)
    notes.extend(key_notes)

    print("Setup check")
    print("-----------")
    for note in notes:
        print(f"OK  {note}")

    if errors:
        print("\nIssues")
        print("------")
        for error in errors:
            print(f"ERR {error}")
        return 1

    print("\nAll checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
