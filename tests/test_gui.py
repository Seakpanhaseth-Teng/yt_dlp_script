"""Tests for YTDLPDownloader GUI logic methods.

Every test constructs the object via the ``app`` fixture (see conftest.py)
which bypasses __init__ and provides mock widgets.  We call methods
directly and assert effects on the mocks.
"""
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from yt_dlp_script.downloader import DownloadResult


# ── start_download ─────────────────────────────────────────────────────────


class TestStartDownload:
    def test_early_return_when_already_downloading(self, app: Any) -> None:
        app.manager.is_downloading = True
        with patch.object(app.manager, "download") as mock_download:
            app.start_download()
        mock_download.assert_not_called()

    def test_invalid_url_shows_error(self, app: Any) -> None:
        app.url_var.get.return_value = "not-a-valid-url"
        with patch("yt_dlp_script.gui.messagebox.showerror") as mock_error:
            app.start_download()
        mock_error.assert_called_once()
        assert not app.manager.is_downloading

    def test_empty_url_shows_error(self, app: Any) -> None:
        app.url_var.get.return_value = ""
        with patch("yt_dlp_script.gui.messagebox.showerror") as mock_error:
            app.start_download()
        mock_error.assert_called_once()

    def test_folder_not_found_shows_prompt(self, app: Any) -> None:
        app.url_var.get.return_value = "https://youtu.be/test"
        app.folder_var.get.return_value = "/nonexistent/path"
        with patch("yt_dlp_script.gui.messagebox.askyesno", return_value=False), \
             patch("yt_dlp_script.gui.messagebox.showerror") as mock_error:
            app.start_download()
        mock_error.assert_called_once_with("Error", "Folder does not exist.")

    def test_folder_not_found_creates_folder(self, app: Any, tmp_path: Path) -> None:
        new_folder = str(tmp_path / "created_subfolder")
        app.url_var.get.return_value = "https://youtu.be/test"
        app.folder_var.get.return_value = new_folder
        with patch("yt_dlp_script.gui.messagebox.askyesno", return_value=True), \
             patch("yt_dlp_script.gui.os.access", return_value=True):
            app.start_download()
        assert Path(new_folder).exists()

    def test_folder_not_found_created_not_writable(self, app: Any, tmp_path: Path) -> None:
        new_folder = str(tmp_path / "readonly_subfolder")
        app.url_var.get.return_value = "https://youtu.be/test"
        app.folder_var.get.return_value = new_folder
        with patch("yt_dlp_script.gui.messagebox.askyesno", return_value=True), \
             patch("yt_dlp_script.gui.os.access", return_value=False), \
             patch("yt_dlp_script.gui.messagebox.showerror") as mock_error:
            app.start_download()
        mock_error.assert_called_once()
        assert "not writable" in mock_error.call_args[0][1]

    def test_folder_validation_error_shown(self, app: Any) -> None:
        app.url_var.get.return_value = "https://youtu.be/test"
        app.folder_var.get.return_value = ""
        with patch("yt_dlp_script.gui.messagebox.showerror") as mock_error:
            app.start_download()
        mock_error.assert_called_once()

    def test_ffmpeg_warning_shown_when_missing(self, app: Any) -> None:
        app.url_var.get.return_value = "https://youtu.be/test"
        app.manager.ffmpeg_dir = None
        with patch("yt_dlp_script.gui.messagebox.showwarning") as mock_warn:
            app.start_download()
        mock_warn.assert_called_once()

    def test_ffmpeg_warning_not_shown_when_present(self, app: Any) -> None:
        app.url_var.get.return_value = "https://youtu.be/test"
        app.manager.ffmpeg_dir = "/usr/bin"
        with patch("yt_dlp_script.gui.messagebox.showwarning") as mock_warn:
            app.start_download()
        mock_warn.assert_not_called()

    def test_button_states_on_start(self, app: Any) -> None:
        app.url_var.get.return_value = "https://youtu.be/test"
        with patch("yt_dlp_script.gui.threading.Thread") as mock_thread, \
             patch("yt_dlp_script.gui.messagebox.showwarning"):
            app.start_download()
        app.download_btn.configure.assert_any_call(state="disabled")
        app.cancel_btn.configure.assert_any_call(state="normal")
        app.status_label.configure.assert_any_call(text="Downloading...")
        app.progress_bar.set.assert_any_call(0)

    def test_starts_thread_with_correct_args(self, app: Any) -> None:
        url = "https://youtu.be/test"
        folder = str(Path.home() / "Downloads")
        app.url_var.get.return_value = url
        app.folder_var.get.return_value = folder
        app.resolution_var.get.return_value = "720p"
        app.audio_var.get.return_value = "mp3"
        app.video_format_var.get.return_value = "mkv"
        app.ssl_bypass_var.get.return_value = True
        app.playlist_var.get.return_value = True

        with patch("yt_dlp_script.gui.threading.Thread") as mock_thread, \
             patch("yt_dlp_script.gui.messagebox.showwarning"):
            app.start_download()

        mock_thread.assert_called_once()
        _call_args = mock_thread.call_args[1]
        assert _call_args["target"] == app._run_download
        assert _call_args["args"] == (url, folder, "720p", "mp3", "mkv", True, True)
        assert _call_args["daemon"] is True
        mock_thread.return_value.start.assert_called_once()

    def test_manager_reset_called(self, app: Any) -> None:
        app.url_var.get.return_value = "https://youtu.be/test"
        app.manager.cancel_event.set()
        with patch("yt_dlp_script.gui.threading.Thread"), \
             patch("yt_dlp_script.gui.messagebox.showwarning"):
            app.start_download()
        assert not app.manager.cancel_event.is_set()


# ── cancel_download ────────────────────────────────────────────────────────


class TestCancelDownload:
    def test_sets_cancel_event(self, app: Any) -> None:
        app.cancel_download()
        assert app.manager.cancel_event.is_set()

    def test_updates_status_label(self, app: Any) -> None:
        app.cancel_download()
        app.status_label.configure.assert_called_with(text="Cancelling...")


# ── _on_version_check ──────────────────────────────────────────────────────


class TestOnVersionCheck:
    def test_no_ytdlp_detected(self, app: Any) -> None:
        app._on_version_check(None, None)
        app.status_label.configure.assert_called_with(
            text="Could not detect yt-dlp version"
        )

    def test_update_available(self, app: Any) -> None:
        app._on_version_check("2024.1", "2024.2")
        app.status_label.configure.assert_called_with(
            text="Update available: 2024.1 to 2024.2"
        )

    def test_up_to_date(self, app: Any) -> None:
        app._on_version_check("2024.1", "2024.1")
        app.status_label.configure.assert_called_with(
            text="yt-dlp is up to date"
        )

    def test_no_latest_version_but_current_exists(self, app: Any) -> None:
        app._on_version_check("2024.1", None)
        app.status_label.configure.assert_called_with(
            text="yt-dlp is up to date"
        )


# ── do_update / _on_update_result ─────────────────────────────────────────


class TestDoUpdate:
    def test_disables_button_and_updates_status(self, app: Any) -> None:
        with patch("yt_dlp_script.gui.threading.Thread") as mock_thread:
            app.do_update()
        app.status_label.configure.assert_any_call(text="Updating yt-dlp...")
        app.update_btn.configure.assert_any_call(state="disabled")
        mock_thread.assert_called_once()
        mock_thread.return_value.start.assert_called_once()

    def test_on_update_result_re_enables_button(self, app: Any) -> None:
        app._on_update_result("Update successful!")
        app.status_label.configure.assert_called_with(text="Update successful!")
        app.update_btn.configure.assert_called_with(state="normal")


# ── browse_folder ──────────────────────────────────────────────────────────


class TestBrowseFolder:
    def test_sets_folder_when_selected(self, app: Any) -> None:
        chosen = "/some/folder"
        with patch("yt_dlp_script.gui.filedialog.askdirectory",
                   return_value=chosen):
            app.browse_folder()
        app.folder_var.set.assert_called_with(chosen)

    def test_does_not_change_when_cancelled(self, app: Any) -> None:
        with patch("yt_dlp_script.gui.filedialog.askdirectory",
                   return_value=""):
            app.browse_folder()
        app.folder_var.set.assert_not_called()


# ── _run_download ──────────────────────────────────────────────────────────


class TestRunDownload:
    def test_calls_manager_download_with_args(self, app: Any) -> None:
        result = DownloadResult(True, "done")
        with patch.object(app.manager, "download", return_value=result) as mock_dl:
            app._run_download(
                url="https://youtu.be/x",
                folder="/tmp",
                resolution="1080p",
                audio_format="None",
                video_format="mp4",
                ssl_bypass=False,
                playlist=True,
            )
        mock_dl.assert_called_once_with(
            url="https://youtu.be/x",
            folder="/tmp",
            resolution="1080p",
            audio_format="None",
            video_format="mp4",
            ssl_bypass=False,
            playlist=True,
        )

    def test_schedules_completion_via_after(self, app: Any) -> None:
        result = DownloadResult(True, "done")
        with patch.object(app.manager, "download", return_value=result):
            app._run_download(
                url="https://youtu.be/x",
                folder="/tmp",
                resolution="1080p",
                audio_format="None",
                video_format="mp4",
                ssl_bypass=False,
            )
        app.after.assert_called_once()
        args = app.after.call_args[0]
        assert args[0] == 0  # first arg is milliseconds


# ── _on_progress_hook ──────────────────────────────────────────────────────


class TestOnProgressHook:
    def test_downloading_updates_progress_and_status(self, app: Any) -> None:
        data = {"status": "downloading",
                "_percent_str": "45.0%", "eta": 30}
        app._on_progress_hook(data)
        assert app.after.call_count > 0

    def test_finished_sets_progress_100_and_processing(self, app: Any) -> None:
        data = {"status": "finished"}
        app._on_progress_hook(data)
        assert app.after.call_count >= 2

    def test_error_sets_status_text(self, app: Any) -> None:
        data = {"status": "error"}
        app._on_progress_hook(data)
        app.after.assert_called_once()
        _cb = app.after.call_args[0][1]
        with patch.object(app.status_label, "configure") as mock_cfg:
            _cb()
        mock_cfg.assert_called_with(text="Error during download")


# ── _on_download_complete ──────────────────────────────────────────────────


class TestOnDownloadComplete:
    def test_success_sets_progress_100(self, app: Any) -> None:
        result = DownloadResult(True, "Download complete!")
        with patch("yt_dlp_script.gui.messagebox.showerror") as mock_err:
            app._on_download_complete(result)
        app.progress_bar.set.assert_called_with(1)
        mock_err.assert_not_called()

    def test_failure_sets_progress_0_and_shows_error(self, app: Any) -> None:
        result = DownloadResult(False, "Something went wrong")
        with patch("yt_dlp_script.gui.messagebox.showerror") as mock_err:
            app._on_download_complete(result)
        app.progress_bar.set.assert_called_with(0)
        mock_err.assert_called_once_with("Download Failed", "Something went wrong")

    def test_restores_button_states(self, app: Any) -> None:
        result = DownloadResult(True, "done")
        with patch("yt_dlp_script.gui.messagebox.showerror"):
            app._on_download_complete(result)
        app.download_btn.configure.assert_any_call(state="normal")
        app.cancel_btn.configure.assert_any_call(state="disabled")

    def test_updates_status_label(self, app: Any) -> None:
        result = DownloadResult(False, "Error occurred")
        with patch("yt_dlp_script.gui.messagebox.showerror"):
            app._on_download_complete(result)
        app.status_label.configure.assert_any_call(text="Error occurred")
