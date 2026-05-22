import logging
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Optional

import yt_dlp

from yt_dlp_script.config import (
    DEFAULT_AUDIO_QUALITY,
    MAX_FRAGMENT_RETRIES,
    MAX_RETRIES,
)
from yt_dlp_script.exceptions import DownloadCancelledError
from yt_dlp_script.utils import detect_ffmpeg

logger = logging.getLogger(__name__)

ProgressHook = Callable[[dict[str, Any]], None]


@dataclass(frozen=True)
class DownloadResult:
    success: bool
    message: str


class DownloadManager:
    def __init__(self) -> None:
        self.ffmpeg_dir: Optional[str] = detect_ffmpeg()
        self.cancel_event: threading.Event = threading.Event()
        self.is_downloading: bool = False
        self._progress_callbacks: list[ProgressHook] = []

    def on_progress(self, callback: ProgressHook) -> None:
        self._progress_callbacks.append(callback)

    def _notify_progress(self, data: dict[str, Any]) -> None:
        for callback in self._progress_callbacks:
            callback(data)

    def cancel(self) -> None:
        self.cancel_event.set()
        logger.info("Download cancellation requested.")

    def reset(self) -> None:
        self.cancel_event.clear()

    def build_options(
        self,
        folder: str,
        resolution: str,
        audio_format: str,
        video_format: str,
        ssl_bypass: bool,
        playlist: bool = False,
    ) -> dict[str, Any]:
        height: str = resolution.replace("p", "")

        ydl_opts: dict[str, Any] = {
            "outtmpl": str(Path(folder) / "%(title)s.%(ext)s"),
            "noplaylist": not playlist,
            "progress_hooks": [self._progress_hook],
            "no_warnings": True,
            "quiet": True,
            "retries": MAX_RETRIES,
            "fragment_retries": MAX_FRAGMENT_RETRIES,
            "geo_bypass": True,
        }

        if playlist:
            ydl_opts["ignoreerrors"] = True

        if self.ffmpeg_dir:
            ydl_opts["ffmpeg_location"] = self.ffmpeg_dir

        if ssl_bypass:
            ydl_opts["nocheckcertificate"] = True
            logger.warning("SSL certificate verification is disabled.")

        if audio_format and audio_format != "None":
            ydl_opts["format"] = "bestaudio/best"
            ydl_opts["postprocessors"] = [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": audio_format,
                    "preferredquality": DEFAULT_AUDIO_QUALITY,
                }
            ]
        else:
            ydl_opts["format"] = (
                f"bestvideo[height<={height}][ext={video_format}]+bestaudio/"
                f"bestvideo[height<={height}]+bestaudio/best[ext={video_format}]/"
                f"bestvideo[height<={height}]+bestaudio/best"
            )
            ydl_opts["postprocessors"] = [
                {
                    "key": "FFmpegVideoConvertor",
                    "preferedformat": video_format,
                }
            ]

        return ydl_opts

    def _progress_hook(self, data: dict[str, Any]) -> None:
        if self.cancel_event.is_set() and data.get("status") == "downloading":
            raise DownloadCancelledError("Download cancelled by user.")
        self._notify_progress(data)

    def download(
        self,
        url: str,
        folder: str,
        resolution: str,
        audio_format: str,
        video_format: str,
        ssl_bypass: bool,
        playlist: bool = False,
    ) -> DownloadResult:
        self.is_downloading = True
        ydl_opts = self.build_options(
            folder=folder,
            resolution=resolution,
            audio_format=audio_format,
            video_format=video_format,
            ssl_bypass=ssl_bypass,
            playlist=playlist,
        )

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            return DownloadResult(True, "Download complete!")

        except DownloadCancelledError:
            return DownloadResult(False, "Download cancelled.")

        except yt_dlp.utils.DownloadError as e:
            return DownloadResult(False, self._classify_error(str(e)))

        except Exception as e:
            return DownloadResult(False, f"Error: {e}")

        finally:
            self.is_downloading = False

    @staticmethod
    def _classify_error(error_msg: str) -> str:
        if "HTTP Error 429" in error_msg:
            return (
                "Rate limited by YouTube. "
                "Please wait a few minutes and try again."
            )
        msg_lower: str = error_msg.lower()
        if "video unavailable" in msg_lower or "geographic" in msg_lower:
            return "Video unavailable in your region. Try using a proxy or VPN."
        if "age-restricted" in msg_lower or "age" in msg_lower:
            return "Video is age-restricted."
        return f"Download error: {error_msg}"

    @staticmethod
    def calculate_progress(data: dict[str, Any]) -> float:
        if data.get("_percent_str"):
            try:
                return (
                    float(data["_percent_str"].replace("%", "").strip()) / 100.0
                )
            except (ValueError, AttributeError):
                pass
        downloaded: Optional[int] = data.get("downloaded_bytes")
        total: Optional[int] = data.get("total_bytes") or data.get(
            "total_bytes_estimate"
        )
        if downloaded and total and total > 0:
            try:
                return downloaded / total
            except (TypeError, ZeroDivisionError):
                pass
        return 0.0
