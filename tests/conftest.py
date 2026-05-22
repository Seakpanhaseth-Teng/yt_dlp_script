"""Test fixtures for GUI tests.

Mock strategy:
  YTDLPDownloader's __init__ creates real CTk widgets (needs display).
  Instead we bypass __init__ and manually wire up mock widget attributes,
  then test each logic method by calling it and inspecting mock call history.
"""
from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

if TYPE_CHECKING:
    from yt_dlp_script.gui import YTDLPDownloader


@pytest.fixture
def app() -> Iterator[YTDLPDownloader]:
    """YTDLPDownloader instance with all widget dependencies mocked.

    Widget attributes are MagicMock objects so we can assert .configure(),
    .pack(), .set() calls.  Tkinter variables are MagicMock with .get() /
    .set() pre-configured with sensible defaults.
    """
    from yt_dlp_script.downloader import DownloadManager
    from yt_dlp_script.gui import YTDLPDownloader

    # Bypass __init__ (which creates real CTk widgets)
    with patch.object(YTDLPDownloader, "__init__", return_value=None):
        obj = YTDLPDownloader.__new__(YTDLPDownloader)

    # ── Real dependencies ──────────────────────────────────────────────
    obj.manager = DownloadManager()

    # ── Mock tkinter variables ─────────────────────────────────────────
    def _make_var(default: object = "") -> MagicMock:
        m: MagicMock = MagicMock()
        m.get.return_value = default
        return m

    obj.url_var = _make_var("")
    obj.folder_var = _make_var(str(Path.home() / "Downloads"))
    obj.resolution_var = _make_var("1080p")
    obj.audio_var = _make_var("None")
    obj.video_format_var = _make_var("mp4")
    obj.ssl_bypass_var = _make_var(False)
    obj.playlist_var = _make_var(False)

    # ── Mock widgets (every attribute set in _create_widgets) ───────────
    for widget_name in (
        "url_label",
        "url_entry",
        "folder_label",
        "folder_entry",
        "browse_btn",
        "res_label",
        "res_dropdown",
        "audio_label",
        "audio_dropdown",
        "video_format_label",
        "video_format_dropdown",
        "update_btn",
        "download_btn",
        "cancel_btn",
        "progress_bar",
        "status_label",
    ):
        setattr(obj, widget_name, MagicMock(name=widget_name))

    # Mock frames
    for frame_name in ("folder_frame", "options_frame", "button_frame",
                       "resolution_frame", "audio_frame", "format_frame",
                       "ssl_frame"):
        setattr(obj, frame_name, MagicMock(name=frame_name))

    # Checkboxes
    obj.ssl_checkbox = MagicMock(name="ssl_checkbox")
    obj.playlist_checkbox = MagicMock(name="playlist_checkbox")

    # CTk base class methods used directly on self
    obj.after = MagicMock(name="after")

    # ── Wire manager callback ──────────────────────────────────────────
    obj.manager.on_progress(obj._on_progress_hook)

    yield obj
