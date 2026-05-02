"""Absolute paths for templates/static — Render (and others) cwd is not guaranteed to be repo root."""

from pathlib import Path

# Directory of the `app` package (.../EventSphere-Platform/app)
APP_DIR = Path(__file__).resolve().parent
