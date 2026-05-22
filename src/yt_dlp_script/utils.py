import importlib.metadata
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Optional

from yt_dlp_script.config import (
    FFMPEG_EXECUTABLE,
    PIP_TIMEOUT,
    PROJECT_ROOT,
    PYPI_API_URL,
    PYPI_TIMEOUT,
)
from yt_dlp_script.exceptions import (
    FolderNotFoundError,
    FolderNotWritableError,
    ValidationError,
)

logger = logging.getLogger(__name__)

BUNDLED_FFMPEG_DIR: Path = (
    PROJECT_ROOT
    / "ffmpeg-master-latest-win64-gpl"
    / "ffmpeg-master-latest-win64-gpl"
    / "bin"
)

URL_PATTERN: re.Pattern[str] = re.compile(
    r"^(https?://)?"
    r"((www|music|m)\.)?"
    r"(youtube\.com/(watch\?|shorts/|playlist\?|live/|embed/)|youtu\.be/)"
    r".+"
    r"$",
    re.IGNORECASE,
)


def validate_url(url: str) -> None:
    if not url:
        raise ValidationError("Please enter a URL.")
    if not URL_PATTERN.match(url):
        raise ValidationError("Invalid URL. Please enter a valid YouTube URL.")


def validate_folder(folder: str) -> None:
    if not folder:
        raise ValidationError("Please select a folder to save the file.")
    path = Path(folder)
    if not path.exists():
        raise FolderNotFoundError(
            f"The folder '{folder}' does not exist.\nWould you like to create it?"
        )
    if not os.access(folder, os.W_OK):
        raise FolderNotWritableError(
            "Folder is not writable. Please choose a different location."
        )


def detect_ffmpeg() -> Optional[str]:
    bundled_exe = BUNDLED_FFMPEG_DIR / FFMPEG_EXECUTABLE
    if bundled_exe.exists():
        logger.info("Using bundled ffmpeg: %s", BUNDLED_FFMPEG_DIR)
        return str(BUNDLED_FFMPEG_DIR)
    system_ffmpeg: Optional[str] = shutil.which("ffmpeg")
    if system_ffmpeg:
        ffmpeg_dir: str = os.path.dirname(system_ffmpeg)
        logger.info("Using system ffmpeg: %s", ffmpeg_dir)
        return ffmpeg_dir
    logger.warning("ffmpeg not found. Video/audio processing may fail.")
    return None


def get_current_version() -> Optional[str]:
    try:
        return importlib.metadata.version("yt-dlp")
    except importlib.metadata.PackageNotFoundError:
        return None


def fetch_latest_version() -> Optional[str]:
    try:
        with urllib.request.urlopen(PYPI_API_URL, timeout=PYPI_TIMEOUT) as response:
            data: dict[str, Any] = json.loads(response.read().decode())
            version: str = data["info"]["version"]
            return version
    except (urllib.error.URLError, json.JSONDecodeError, KeyError):
        return None


def format_eta(data: dict[str, Any]) -> str:
    eta_str: Optional[str] = data.get("_eta_str")
    if eta_str:
        return eta_str
    eta_seconds: Optional[int] = data.get("eta")
    if eta_seconds is not None:
        minutes: int = eta_seconds // 60
        seconds: int = eta_seconds % 60
        return f"{minutes:02d}:{seconds:02d}"
    return "?"


def update_yt_dlp() -> str:
    if sys.prefix == sys.base_prefix:
        return (
            "Update requires a virtual environment. "
            "Activate a venv and try again."
        )

    try:
        result: subprocess.CompletedProcess[str] = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"],
            capture_output=True,
            text=True,
            timeout=PIP_TIMEOUT,
        )
        if result.returncode == 0:
            return "Update successful! Please restart the application."
        return f"Update failed: {result.stderr}"
    except subprocess.TimeoutExpired:
        return "Update failed: timed out."
    except subprocess.CalledProcessError as e:
        return f"Update failed: {e}"
    except OSError as e:
        return f"Update failed: {e}"
