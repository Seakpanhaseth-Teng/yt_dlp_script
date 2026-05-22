from collections.abc import Iterator
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from yt_dlp_script.downloader import DownloadManager, DownloadResult
from yt_dlp_script.exceptions import DownloadCancelledError


@pytest.fixture
def manager() -> Iterator[DownloadManager]:
    with patch("yt_dlp_script.downloader.detect_ffmpeg", return_value=None):
        yield DownloadManager()


class TestBuildOptions:
    def test_video_options(self, manager: DownloadManager) -> None:
        opts = manager.build_options(
            folder="/tmp",
            resolution="1080p",
            audio_format="None",
            video_format="mp4",
            ssl_bypass=False,
        )
        expected_outtmpl: str = str(Path("/tmp") / "%(title)s.%(ext)s")
        assert opts["outtmpl"] == expected_outtmpl
        assert opts["noplaylist"] is True
        assert opts["retries"] == 5
        assert "FFmpegVideoConvertor" in str(opts["postprocessors"])
        assert "bestvideo[height<=1080][ext=mp4]" in opts["format"]

    def test_audio_options(self, manager: DownloadManager) -> None:
        opts = manager.build_options(
            folder="/tmp",
            resolution="1080p",
            audio_format="mp3",
            video_format="mp4",
            ssl_bypass=False,
        )
        assert opts["format"] == "bestaudio/best"
        extractor = opts["postprocessors"][0]
        assert extractor["key"] == "FFmpegExtractAudio"
        assert extractor["preferredcodec"] == "mp3"

    def test_ffmpeg_location(self, manager: DownloadManager) -> None:
        manager.ffmpeg_dir = "/usr/bin"
        opts = manager.build_options(
            folder="/tmp",
            resolution="720p",
            audio_format="None",
            video_format="mkv",
            ssl_bypass=False,
        )
        assert opts["ffmpeg_location"] == "/usr/bin"

    def test_ssl_bypass(self, manager: DownloadManager) -> None:
        opts = manager.build_options(
            folder="/tmp",
            resolution="720p",
            audio_format="None",
            video_format="mp4",
            ssl_bypass=True,
        )
        assert opts["nocheckcertificate"] is True

    def test_playlist_mode(self, manager: DownloadManager) -> None:
        opts = manager.build_options(
            folder="/tmp",
            resolution="1080p",
            audio_format="None",
            video_format="mp4",
            ssl_bypass=False,
            playlist=True,
        )
        assert opts["noplaylist"] is False
        assert opts["ignoreerrors"] is True

    def test_no_ffmpeg_location_when_missing(
        self, manager: DownloadManager
    ) -> None:
        manager.ffmpeg_dir = None
        opts = manager.build_options(
            folder="/tmp",
            resolution="720p",
            audio_format="None",
            video_format="mp4",
            ssl_bypass=False,
        )
        assert "ffmpeg_location" not in opts


class TestCalculateProgress:
    def test_from_percent_str(self, manager: DownloadManager) -> None:
        result = manager.calculate_progress(
            {"_percent_str": "42.50%"}
        )
        assert abs(result - 0.425) < 0.001

    def test_from_percent_str_no_sign(self, manager: DownloadManager) -> None:
        result = manager.calculate_progress(
            {"_percent_str": "100%"}
        )
        assert abs(result - 1.0) < 0.001

    def test_from_bytes(self, manager: DownloadManager) -> None:
        result = manager.calculate_progress(
            {"downloaded_bytes": 500, "total_bytes": 1000}
        )
        assert abs(result - 0.5) < 0.001

    def test_from_bytes_estimate(self, manager: DownloadManager) -> None:
        result = manager.calculate_progress(
            {"downloaded_bytes": 250, "total_bytes_estimate": 1000}
        )
        assert abs(result - 0.25) < 0.001

    def test_fallback_zero(self, manager: DownloadManager) -> None:
        result = manager.calculate_progress({})
        assert result == 0.0

    def test_division_by_zero(self, manager: DownloadManager) -> None:
        result = manager.calculate_progress(
            {"downloaded_bytes": 500, "total_bytes": 0}
        )
        assert result == 0.0


class TestClassifyError:
    def test_rate_limit(self) -> None:
        msg = DownloadManager._classify_error("HTTP Error 429: Too Many Requests")
        assert "rate limited" in msg.lower()

    def test_geo_restricted_case_insensitive(self) -> None:
        msg = DownloadManager._classify_error(
            "Video unavailable: This video is not available in your geographic region"
        )
        assert "region" in msg or "vpn" in msg

    def test_geo_restricted_lowercase(self) -> None:
        msg = DownloadManager._classify_error(
            "video unavailable: geographic restriction"
        )
        assert "region" in msg or "vpn" in msg

    def test_age_restricted(self) -> None:
        msg = DownloadManager._classify_error(
            "Sign in to confirm your age: This video is age-restricted"
        )
        assert "age" in msg.lower()

    def test_age_restricted_lowercase_only(self) -> None:
        msg = DownloadManager._classify_error(
            "age-restricted content"
        )
        assert "age" in msg.lower()

    def test_generic_error(self) -> None:
        msg = DownloadManager._classify_error("Some random error")
        assert "download error" in msg.lower()


class TestDownload:
    @patch("yt_dlp_script.downloader.yt_dlp.YoutubeDL")
    def test_download_success(
        self, mock_ydl_cls: MagicMock, manager: DownloadManager
    ) -> None:
        mock_ydl = MagicMock()
        mock_ydl_cls.return_value.__enter__.return_value = mock_ydl

        result = manager.download(
            url="https://youtu.be/test",
            folder="/tmp",
            resolution="1080p",
            audio_format="None",
            video_format="mp4",
            ssl_bypass=False,
        )

        assert result.success is True
        assert "complete" in result.message
        mock_ydl.download.assert_called_once_with(
            ["https://youtu.be/test"]
        )

    @patch("yt_dlp_script.downloader.yt_dlp.YoutubeDL")
    def test_download_cancelled_during_download(
        self, mock_ydl_cls: MagicMock, manager: DownloadManager
    ) -> None:
        mock_ydl = MagicMock()
        mock_ydl.download.side_effect = DownloadCancelledError("cancelled")
        mock_ydl_cls.return_value.__enter__.return_value = mock_ydl

        result = manager.download(
            url="https://youtu.be/test",
            folder="/tmp",
            resolution="1080p",
            audio_format="None",
            video_format="mp4",
            ssl_bypass=False,
        )

        assert result.success is False
        assert "cancelled" in result.message

    @patch(
        "yt_dlp_script.downloader.yt_dlp.YoutubeDL",
        side_effect=Exception("Network error"),
    )
    def test_download_unexpected_error(
        self, mock_ydl_cls: MagicMock, manager: DownloadManager
    ) -> None:
        result = manager.download(
            url="https://youtu.be/test",
            folder="/tmp",
            resolution="1080p",
            audio_format="None",
            video_format="mp4",
            ssl_bypass=False,
        )

        assert result.success is False
        assert "Error" in result.message

    def test_cancel_method(self, manager: DownloadManager) -> None:
        assert not manager.cancel_event.is_set()
        manager.cancel()
        assert manager.cancel_event.is_set()

    def test_reset_method(self, manager: DownloadManager) -> None:
        manager.cancel()
        assert manager.cancel_event.is_set()
        manager.reset()
        assert not manager.cancel_event.is_set()
