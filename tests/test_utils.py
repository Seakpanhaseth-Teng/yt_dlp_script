import importlib.metadata
import subprocess
import urllib.error
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from yt_dlp_script.exceptions import (
    FolderNotFoundError,
    FolderNotWritableError,
    ValidationError,
)
from yt_dlp_script.utils import (
    URL_PATTERN,
    detect_ffmpeg,
    fetch_latest_version,
    format_eta,
    get_current_version,
    update_yt_dlp,
    validate_folder,
    validate_url,
)


class TestValidateURL:
    def test_valid_youtube_watch(self) -> None:
        validate_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

    def test_valid_youtu_be(self) -> None:
        validate_url("https://youtu.be/dQw4w9WgXcQ")

    def test_valid_shorts(self) -> None:
        validate_url("https://www.youtube.com/shorts/abc123")

    def test_valid_embed(self) -> None:
        validate_url("https://www.youtube.com/embed/dQw4w9WgXcQ")

    def test_valid_playlist(self) -> None:
        validate_url(
            "https://www.youtube.com/playlist?list=PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf"
        )

    def test_valid_playlist_without_www(self) -> None:
        validate_url("https://youtube.com/playlist?list=PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf")

    def test_valid_music_subdomain(self) -> None:
        validate_url("https://music.youtube.com/watch?v=dQw4w9WgXcQ")

    def test_valid_mobile_subdomain(self) -> None:
        validate_url("https://m.youtube.com/watch?v=dQw4w9WgXcQ")

    def test_valid_live(self) -> None:
        validate_url("https://www.youtube.com/live/dQw4w9WgXcQ")

    def test_valid_with_extra_params(self) -> None:
        validate_url(
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ&list=PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf&index=1"
        )

    def test_valid_with_feature_param(self) -> None:
        validate_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ&feature=shared")

    def test_valid_with_time_param(self) -> None:
        validate_url("https://youtu.be/dQw4w9WgXcQ?t=30")

    def test_valid_without_scheme(self) -> None:
        validate_url("www.youtube.com/watch?v=dQw4w9WgXcQ")

    def test_empty_url_raises(self) -> None:
        with pytest.raises(ValidationError, match="Please enter a URL"):
            validate_url("")

    def test_invalid_url_raises(self) -> None:
        with pytest.raises(ValidationError, match="Invalid URL"):
            validate_url("https://example.com")

    def test_random_string_raises(self) -> None:
        with pytest.raises(ValidationError, match="Invalid URL"):
            validate_url("not a url at all")

    def test_url_pattern_rejects_non_youtube(self) -> None:
        assert not URL_PATTERN.match("https://vimeo.com/12345")

    def test_url_pattern_matches_youtube(self) -> None:
        assert URL_PATTERN.match("https://www.youtube.com/watch?v=abc123")


class TestValidateFolder:
    @patch("yt_dlp_script.utils.Path.exists", return_value=True)
    @patch("yt_dlp_script.utils.os.access", return_value=True)
    def test_folder_exists_and_writable(
        self, mock_access: MagicMock, mock_exists: MagicMock
    ) -> None:
        validate_folder("C:\\Users\\test\\Downloads")

    @patch("yt_dlp_script.utils.Path.exists", return_value=True)
    @patch("yt_dlp_script.utils.os.access", return_value=False)
    def test_folder_not_writable(
        self, mock_access: MagicMock, mock_exists: MagicMock
    ) -> None:
        with pytest.raises(FolderNotWritableError):
            validate_folder("C:\\Users\\test\\ReadOnly")

    @patch("yt_dlp_script.utils.Path.exists", return_value=False)
    def test_folder_does_not_exist(
        self, mock_exists: MagicMock
    ) -> None:
        with pytest.raises(FolderNotFoundError):
            validate_folder("C:\\Nonexistent\\Folder")

    def test_empty_folder_raises(self) -> None:
        with pytest.raises(ValidationError, match="Please select a folder"):
            validate_folder("")


class TestDetectFFmpeg:
    @patch("yt_dlp_script.utils.BUNDLED_FFMPEG_DIR")
    def test_bundled_ffmpeg_found(
        self, mock_bundled: MagicMock
    ) -> None:
        bundled_exe = mock_bundled.__truediv__.return_value
        bundled_exe.exists.return_value = True
        result = detect_ffmpeg()
        assert result is not None

    @patch("yt_dlp_script.utils.BUNDLED_FFMPEG_DIR")
    @patch("yt_dlp_script.utils.shutil.which", return_value="/usr/bin/ffmpeg")
    def test_system_ffmpeg_found(
        self, mock_which: MagicMock, mock_bundled: MagicMock
    ) -> None:
        bundled_exe = mock_bundled.__truediv__.return_value
        bundled_exe.exists.return_value = False
        result = detect_ffmpeg()
        assert result is not None
        assert "usr" in result

    @patch("yt_dlp_script.utils.BUNDLED_FFMPEG_DIR")
    @patch("yt_dlp_script.utils.shutil.which", return_value=None)
    def test_no_ffmpeg_found(
        self, mock_which: MagicMock, mock_bundled: MagicMock
    ) -> None:
        bundled_exe = mock_bundled.__truediv__.return_value
        bundled_exe.exists.return_value = False
        result = detect_ffmpeg()
        assert result is None


class TestVersion:
    @patch("yt_dlp_script.utils.importlib.metadata.version", return_value="2024.1.0")
    def test_get_current_version(self, mock_version: MagicMock) -> None:
        assert get_current_version() == "2024.1.0"

    @patch(
        "yt_dlp_script.utils.importlib.metadata.version",
        side_effect=importlib.metadata.PackageNotFoundError,
    )
    def test_get_current_version_failure(self, mock_version: MagicMock) -> None:
        assert get_current_version() is None

    @patch("yt_dlp_script.utils.urllib.request.urlopen")
    def test_fetch_latest_version(self, mock_urlopen: MagicMock) -> None:
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"info": {"version": "2024.2.0"}}'
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response
        assert fetch_latest_version() == "2024.2.0"

    @patch(
        "yt_dlp_script.utils.urllib.request.urlopen",
        side_effect=urllib.error.URLError("network error"),
    )
    def test_fetch_latest_version_failure(self, mock_urlopen: MagicMock) -> None:
        assert fetch_latest_version() is None


class TestFormatETA:
    def test_from_eta_str(self) -> None:
        assert format_eta({"_eta_str": "00:42"}) == "00:42"

    def test_from_eta_seconds(self) -> None:
        assert format_eta({"eta": 125}) == "02:05"

    def test_from_eta_seconds_zero(self) -> None:
        assert format_eta({"eta": 0}) == "00:00"

    def test_fallback(self) -> None:
        assert format_eta({}) == "?"

    def test_eta_str_preferred(self) -> None:
        assert format_eta({"_eta_str": "01:30", "eta": 999}) == "01:30"


class TestUpdate:
    VENV_PATCH = [
        patch("yt_dlp_script.utils.sys.prefix", "/venv"),
        patch("yt_dlp_script.utils.sys.base_prefix", "/system"),
    ]

    def _setup_venv(self) -> None:
        for p in self.VENV_PATCH:
            p.start()

    def _teardown_venv(self) -> None:
        for p in self.VENV_PATCH:
            p.stop()

    @patch(
        "yt_dlp_script.utils.subprocess.run",
        return_value=MagicMock(returncode=0),
    )
    def test_update_success(self, mock_run: MagicMock) -> None:
        self._setup_venv()
        try:
            result = update_yt_dlp()
            assert "successful" in result.lower()
        finally:
            self._teardown_venv()

    @patch(
        "yt_dlp_script.utils.subprocess.run",
        return_value=MagicMock(returncode=1, stderr="error message"),
    )
    def test_update_failure(self, mock_run: MagicMock) -> None:
        self._setup_venv()
        try:
            result = update_yt_dlp()
            assert "failed" in result.lower()
        finally:
            self._teardown_venv()

    def test_update_no_venv_returns_warning(self) -> None:
        with patch("yt_dlp_script.utils.sys.prefix", "/system"), \
             patch("yt_dlp_script.utils.sys.base_prefix", "/system"):
            result = update_yt_dlp()
        assert "virtual environment" in result.lower()

    @patch(
        "yt_dlp_script.utils.subprocess.run",
        side_effect=subprocess.TimeoutExpired(cmd=["pip"], timeout=30),
    )
    def test_update_timeout(self, mock_run: MagicMock) -> None:
        self._setup_venv()
        try:
            result = update_yt_dlp()
            assert "timed out" in result.lower()
        finally:
            self._teardown_venv()

    @patch(
        "yt_dlp_script.utils.subprocess.run",
        side_effect=OSError("permission denied"),
    )
    def test_update_os_error(self, mock_run: MagicMock) -> None:
        self._setup_venv()
        try:
            result = update_yt_dlp()
            assert "permission denied" in result.lower()
        finally:
            self._teardown_venv()
