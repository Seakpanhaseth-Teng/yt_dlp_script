import json
import logging
import os
import re
import shutil
import subprocess
import sys
import threading
import urllib.request
from tkinter import filedialog, messagebox
from typing import Optional

import tkinter as tk
import customtkinter as ctk
import yt_dlp

# ─── Constants ───────────────────────────────────────────────────────────────

# Colors
PRIMARY_COLOR: str = "#1AABFF"
BG_COLOR: str = "#000000"
HOVER_COLOR: str = "#B20000"
UPDATE_BTN_COLOR: str = "#444444"
CANCEL_BTN_COLOR: str = "#CC3333"
CANCEL_BTN_TEXT_COLOR: str = "#FFFFFF"

# Dimensions
WINDOW_GEOMETRY: str = "550x520"
WINDOW_RESIZABLE: tuple[bool, bool] = (False, False)
ENTRY_WIDTH_MAIN: int = 450
ENTRY_WIDTH_FOLDER: int = 280
BUTTON_WIDTH_DOWNLOAD: int = 200
BUTTON_WIDTH_CANCEL: int = 120
BUTTON_WIDTH_UPDATE: int = 200
BUTTON_HEIGHT_SMALL: int = 30
BUTTON_HEIGHT_LARGE: int = 40
PROGRESS_BAR_HEIGHT: int = 20
PROGRESS_BAR_WIDTH: int = 450
WRAP_LENGTH: int = 450
FRAME_PADX: int = 40

# Padding presets
PAD_Y_TOP: tuple[int, int] = (20, 5)
PAD_Y_DEFAULT: int = 5
PAD_Y_BUTTON: tuple[int, int] = (10, 10)
PAD_Y_PROGRESS: tuple[int, int] = (0, 5)
PAD_Y_STATUS: tuple[int, int] = (0, 10)
PAD_Y_SSL: tuple[int, int] = (5, 5)
PAD_Y_UPDATE: tuple[int, int] = (5, 10)
PAD_X_LABEL: tuple[int, int] = (10, 5)
PAD_X_FRAME: int = 10
PAD_X_RES: int = 5
PAD_X_BROWSE: int = 5
PAD_X_SSL: int = 10
PAD_X_BUTTON: int = 10
PAD_X_PROGRESS: int = 40

# Fonts
FONT_NAME: str = "Segoe UI"
FONT_SIZE: int = 13
FONT_BOLD_SIZE: int = 15
FONT: tuple[str, int] = (FONT_NAME, FONT_SIZE)
FONT_BOLD: tuple[str, int, str] = (FONT_NAME, FONT_BOLD_SIZE, "bold")

# Timeouts
PIP_TIMEOUT: int = 120
PYPI_TIMEOUT: int = 5

# Download settings
DEFAULT_RESOLUTION: str = "1080p"
DEFAULT_AUDIO: str = "None"
DEFAULT_VIDEO_FORMAT: str = "mp4"
DEFAULT_AUDIO_QUALITY: str = "192"
MAX_RETRIES: int = 5
MAX_FRAGMENT_RETRIES: int = 5

# URLs
PYPI_API_URL: str = "https://pypi.org/pypi/yt-dlp/json"

# File paths
FFMPEG_EXECUTABLE: str = "ffmpeg.exe"

# ─── Application Setup ───────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

URL_PATTERN: re.Pattern[str] = re.compile(
    r'^(https?://)?(www\.)?'
    r'(youtube\.com/(watch\?v=|shorts/|playlist\?list=)|'
    r'youtu\.be/|'
    r'youtube\.com/embed/)'
    r'[\w-]+',
    re.IGNORECASE,
)

SCRIPT_DIR: str = os.path.dirname(os.path.abspath(__file__))
BUNDLED_FFMPEG_DIR: str = os.path.join(
    SCRIPT_DIR, "ffmpeg-master-latest-win64-gpl", "ffmpeg-master-latest-win64-gpl", "bin"
)


# ─── Helper Functions ────────────────────────────────────────────────────────


def detect_ffmpeg() -> Optional[str]:
    if os.path.exists(os.path.join(BUNDLED_FFMPEG_DIR, FFMPEG_EXECUTABLE)):
        logger.info(f"Using bundled ffmpeg: {BUNDLED_FFMPEG_DIR}")
        return BUNDLED_FFMPEG_DIR
    system_ffmpeg: Optional[str] = shutil.which("ffmpeg")
    if system_ffmpeg:
        ffmpeg_dir: str = os.path.dirname(system_ffmpeg)
        logger.info(f"Using system ffmpeg: {ffmpeg_dir}")
        return ffmpeg_dir
    logger.warning("ffmpeg not found. Video/audio processing may fail.")
    return None


def validate_url(url: str) -> tuple[bool, str]:
    if not url:
        return False, "Please enter a URL."
    if not URL_PATTERN.match(url):
        return False, "Invalid URL. Please enter a valid YouTube URL."
    return True, ""


def validate_folder(folder: str) -> tuple[bool, str]:
    if not folder:
        return False, "Please select a folder to save the file."
    if not os.path.exists(folder):
        response: bool = messagebox.askyesno(
            "Folder Not Found",
            f"The folder '{folder}' does not exist.\nWould you like to create it?",
        )
        if response:
            try:
                os.makedirs(folder, exist_ok=True)
                logger.info(f"Created folder: {folder}")
            except OSError as e:
                return False, f"Failed to create folder: {e}"
        else:
            return False, "Folder does not exist."
    if not os.access(folder, os.W_OK):
        return False, "Folder is not writable. Please choose a different location."
    return True, ""


def get_current_version() -> Optional[str]:
    try:
        import importlib.metadata
        return importlib.metadata.version("yt-dlp")
    except Exception:
        return None


def update_yt_dlp() -> str:
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
    except Exception as e:
        return f"Update failed: {e}"


def check_for_updates() -> tuple[Optional[str], Optional[str]]:
    return get_current_version(), None


# ─── Main Application ────────────────────────────────────────────────────────


class YTDLPDownloader(ctk.CTk):
    url_label: ctk.CTkLabel
    url_entry: ctk.CTkEntry
    folder_frame: ctk.CTkFrame
    folder_label: ctk.CTkLabel
    folder_entry: ctk.CTkEntry
    browse_btn: ctk.CTkButton
    options_frame: ctk.CTkFrame
    resolution_frame: ctk.CTkFrame
    res_label: ctk.CTkLabel
    res_dropdown: ctk.CTkOptionMenu
    audio_frame: ctk.CTkFrame
    audio_label: ctk.CTkLabel
    audio_dropdown: ctk.CTkOptionMenu
    format_frame: ctk.CTkFrame
    video_format_label: ctk.CTkLabel
    video_format_dropdown: ctk.CTkOptionMenu
    ssl_frame: ctk.CTkFrame
    ssl_checkbox: ctk.CTkCheckBox
    update_btn: ctk.CTkButton
    button_frame: ctk.CTkFrame
    download_btn: ctk.CTkButton
    cancel_btn: ctk.CTkButton
    progress_bar: ctk.CTkProgressBar
    status_label: ctk.CTkLabel

    def __init__(self) -> None:
        super().__init__()
        self.title("YouTube Downloader (yt-dlp Wrapper)")
        self.geometry(WINDOW_GEOMETRY)
        self.resizable(*WINDOW_RESIZABLE)
        self.configure(bg=BG_COLOR)

        self.url_var: tk.StringVar = tk.StringVar()
        self.folder_var: tk.StringVar = tk.StringVar(
            value=os.path.join(os.path.expanduser("~"), "Downloads")
        )
        self.resolution_var: tk.StringVar = tk.StringVar(value=DEFAULT_RESOLUTION)
        self.audio_var: tk.StringVar = tk.StringVar(value=DEFAULT_AUDIO)
        self.video_format_var: tk.StringVar = tk.StringVar(value=DEFAULT_VIDEO_FORMAT)
        self.ssl_bypass_var: tk.BooleanVar = tk.BooleanVar(value=False)

        self.is_downloading: bool = False
        self.cancel_event: threading.Event = threading.Event()
        self.ffmpeg_dir: Optional[str] = detect_ffmpeg()

        self.create_widgets()
        threading.Thread(target=self.check_version_thread, daemon=True).start()

    def check_version_thread(self) -> None:
        try:
            current: Optional[str] = get_current_version()
            latest: Optional[str] = None
            try:
                with urllib.request.urlopen(PYPI_API_URL, timeout=PYPI_TIMEOUT) as response:
                    data: dict = json.loads(response.read().decode())
                    latest = data["info"]["version"]
            except Exception:
                pass
            self.after(0, lambda c=current, l=latest: self.on_version_check(c, l))
        except Exception:
            self.after(0, lambda: self.on_version_check(None, None))

    def on_version_check(self, current: Optional[str], latest: Optional[str]) -> None:
        if latest and current and latest != current:
            self.status_label.configure(text=f"Update available: {current} to {latest}")
        elif current:
            self.status_label.configure(text="yt-dlp is up to date")
        else:
            self.status_label.configure(text="Ready")

    def do_update(self) -> None:
        self.status_label.configure(text="Updating yt-dlp...")
        self.update_btn.configure(state="disabled")
        threading.Thread(target=self.update_thread, daemon=True).start()

    def update_thread(self) -> None:
        result: str = update_yt_dlp()
        self.after(0, lambda: self.on_update_result(result))

    def on_update_result(self, message: str) -> None:
        self.status_label.configure(text=message)
        self.update_btn.configure(state="normal")

    def create_widgets(self) -> None:
        self.url_label = ctk.CTkLabel(
            self, text="YouTube URL:", font=FONT_BOLD, text_color=PRIMARY_COLOR
        )
        self.url_label.pack(pady=PAD_Y_TOP)
        self.url_entry = ctk.CTkEntry(
            self,
            textvariable=self.url_var,
            width=ENTRY_WIDTH_MAIN,
            font=FONT,
            fg_color=BG_COLOR,
            text_color=PRIMARY_COLOR,
            border_color=PRIMARY_COLOR,
        )
        self.url_entry.pack(pady=PAD_Y_DEFAULT)
        self.url_entry.bind("<Return>", lambda e: self.start_download())

        self.folder_frame = ctk.CTkFrame(self, fg_color=BG_COLOR)
        self.folder_frame.pack(pady=PAD_Y_DEFAULT, fill="x", padx=FRAME_PADX)
        self.folder_label = ctk.CTkLabel(
            self.folder_frame, text="Save Folder:", font=FONT, text_color=PRIMARY_COLOR
        )
        self.folder_label.pack(side="left", padx=PAD_X_LABEL)
        self.folder_entry = ctk.CTkEntry(
            self.folder_frame,
            textvariable=self.folder_var,
            width=ENTRY_WIDTH_FOLDER,
            font=FONT,
            fg_color=BG_COLOR,
            text_color=PRIMARY_COLOR,
            border_color=PRIMARY_COLOR,
        )
        self.folder_entry.pack(side="left", padx=PAD_X_DEFAULT)
        self.browse_btn = ctk.CTkButton(
            self.folder_frame,
            text="Browse",
            command=self.browse_folder,
            fg_color=PRIMARY_COLOR,
            text_color=BG_COLOR,
            font=FONT_BOLD,
        )
        self.browse_btn.pack(side="left", padx=PAD_X_BROWSE)

        self.options_frame = ctk.CTkFrame(self, fg_color=BG_COLOR)
        self.options_frame.pack(pady=PAD_Y_DEFAULT, fill="x", padx=FRAME_PADX)

        self.resolution_frame = ctk.CTkFrame(self.options_frame, fg_color=BG_COLOR)
        self.resolution_frame.pack(side="left", padx=PAD_X_RES)
        self.res_label = ctk.CTkLabel(
            self.resolution_frame, text="Resolution:", font=FONT, text_color=PRIMARY_COLOR
        )
        self.res_label.pack(side="left", padx=PAD_X_LABEL)
        self.res_dropdown = ctk.CTkOptionMenu(
            self.resolution_frame,
            variable=self.resolution_var,
            values=["2160p", "1440p", "1080p", "720p", "480p", "360p"],
            fg_color=PRIMARY_COLOR,
            button_color=PRIMARY_COLOR,
            button_hover_color=HOVER_COLOR,
            text_color=BG_COLOR,
            font=FONT,
        )
        self.res_dropdown.pack(side="left", padx=PAD_X_DEFAULT)

        self.audio_frame = ctk.CTkFrame(self.options_frame, fg_color=BG_COLOR)
        self.audio_frame.pack(side="left", padx=PAD_X_FRAME)
        self.audio_label = ctk.CTkLabel(
            self.audio_frame, text="Audio:", font=FONT, text_color=PRIMARY_COLOR
        )
        self.audio_label.pack(side="left", padx=PAD_X_LABEL)
        self.audio_dropdown = ctk.CTkOptionMenu(
            self.audio_frame,
            variable=self.audio_var,
            values=["None", "mp3", "m4a", "wav"],
            fg_color=PRIMARY_COLOR,
            button_color=PRIMARY_COLOR,
            button_hover_color=HOVER_COLOR,
            text_color=BG_COLOR,
            font=FONT,
        )
        self.audio_dropdown.pack(side="left", padx=PAD_X_DEFAULT)

        self.format_frame = ctk.CTkFrame(self.options_frame, fg_color=BG_COLOR)
        self.format_frame.pack(side="left", padx=PAD_X_FRAME)
        self.video_format_label = ctk.CTkLabel(
            self.format_frame, text="Format:", font=FONT, text_color=PRIMARY_COLOR
        )
        self.video_format_label.pack(side="left", padx=PAD_X_LABEL)
        self.video_format_dropdown = ctk.CTkOptionMenu(
            self.format_frame,
            variable=self.video_format_var,
            values=["mp4", "mkv", "webm", "mov", "avi", "flv"],
            fg_color=PRIMARY_COLOR,
            button_color=PRIMARY_COLOR,
            button_hover_color=HOVER_COLOR,
            text_color=BG_COLOR,
            font=FONT,
        )
        self.video_format_dropdown.pack(side="left", padx=PAD_X_DEFAULT)

        self.ssl_frame = ctk.CTkFrame(self, fg_color=BG_COLOR)
        self.ssl_frame.pack(pady=PAD_Y_SSL)
        self.ssl_checkbox = ctk.CTkCheckBox(
            self.ssl_frame,
            text="Bypass SSL verification (not recommended)",
            variable=self.ssl_bypass_var,
            text_color=PRIMARY_COLOR,
            font=FONT,
            fg_color=BG_COLOR,
            border_color=PRIMARY_COLOR,
        )
        self.ssl_checkbox.pack(side="left", padx=PAD_X_SSL)

        self.update_btn = ctk.CTkButton(
            self,
            text="Update yt-dlp",
            command=self.do_update,
            width=BUTTON_WIDTH_UPDATE,
            height=BUTTON_HEIGHT_SMALL,
            fg_color=UPDATE_BTN_COLOR,
            text_color=PRIMARY_COLOR,
            font=FONT,
        )
        self.update_btn.pack(pady=PAD_Y_UPDATE)

        self.button_frame = ctk.CTkFrame(self, fg_color=BG_COLOR)
        self.button_frame.pack(pady=PAD_Y_BUTTON)

        self.download_btn = ctk.CTkButton(
            self.button_frame,
            text="Start Download",
            command=self.start_download,
            width=BUTTON_WIDTH_DOWNLOAD,
            height=BUTTON_HEIGHT_LARGE,
            fg_color=PRIMARY_COLOR,
            text_color=BG_COLOR,
            font=FONT_BOLD,
        )
        self.download_btn.pack(side="left", padx=PAD_X_BUTTON)

        self.cancel_btn = ctk.CTkButton(
            self.button_frame,
            text="Cancel",
            command=self.cancel_download,
            width=BUTTON_WIDTH_CANCEL,
            height=BUTTON_HEIGHT_LARGE,
            fg_color=CANCEL_BTN_COLOR,
            text_color=CANCEL_BTN_TEXT_COLOR,
            font=FONT_BOLD,
            state="disabled",
        )
        self.cancel_btn.pack(side="left", padx=PAD_X_BUTTON)

        self.progress_bar = ctk.CTkProgressBar(
            self,
            width=PROGRESS_BAR_WIDTH,
            height=PROGRESS_BAR_HEIGHT,
            fg_color=BG_COLOR,
            progress_color=PRIMARY_COLOR,
        )
        self.progress_bar.set(0)
        self.progress_bar.pack(pady=PAD_Y_PROGRESS)

        self.status_label = ctk.CTkLabel(
            self,
            text="Ready",
            wraplength=WRAP_LENGTH,
            font=FONT,
            text_color=PRIMARY_COLOR,
        )
        self.status_label.pack(pady=PAD_Y_STATUS)

    def browse_folder(self) -> None:
        folder_selected: str = filedialog.askdirectory()
        if folder_selected:
            self.folder_var.set(folder_selected)

    def start_download(self) -> None:
        if self.is_downloading:
            logger.warning("Download already in progress.")
            return

        url: str = self.url_var.get().strip()
        folder: str = self.folder_var.get().strip()
        resolution: str = self.resolution_var.get()
        audio_format: str = self.audio_var.get()
        video_format: str = self.video_format_var.get()

        valid: bool
        error: str
        valid, error = validate_url(url)
        if not valid:
            messagebox.showerror("Error", error)
            return

        valid, error = validate_folder(folder)
        if not valid:
            messagebox.showerror("Error", error)
            return

        if not self.ffmpeg_dir:
            messagebox.showwarning(
                "FFmpeg Not Found",
                "ffmpeg was not found. Video merging and audio extraction may fail.",
            )

        self.is_downloading = True
        self.cancel_event.clear()
        self.status_label.configure(text="Downloading...")
        self.download_btn.configure(state="disabled")
        self.cancel_btn.configure(state="normal")
        self.progress_bar.set(0)

        threading.Thread(
            target=self.run_download,
            args=(url, folder, resolution, audio_format, video_format),
            daemon=True,
        ).start()

    def cancel_download(self) -> None:
        self.cancel_event.set()
        self.status_label.configure(text="Cancelling...")
        logger.info("Download cancellation requested.")

    def run_download(
        self,
        url: str,
        folder: str,
        resolution: str,
        audio_format: str,
        video_format: str,
    ) -> None:
        height: str = resolution.replace("p", "")

        ydl_opts: dict = {
            "outtmpl": f"{folder}/%(title)s.%(ext)s",
            "noplaylist": True,
            "progress_hooks": [self.my_hook],
            "no_warnings": True,
            "quiet": True,
            "retries": MAX_RETRIES,
            "fragment_retries": MAX_FRAGMENT_RETRIES,
            "geo_bypass": True,
        }

        if self.ffmpeg_dir:
            ydl_opts["ffmpeg_location"] = self.ffmpeg_dir

        if self.ssl_bypass_var.get():
            ydl_opts["nocheckcertificate"] = True
            logger.warning("SSL certificate verification is disabled.")

        if audio_format and audio_format != "None":
            ydl_opts["format"] = "bestaudio/best"
            ydl_opts["postprocessors"] = [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": audio_format,
                "preferredquality": DEFAULT_AUDIO_QUALITY,
            }]
        else:
            ydl_opts["format"] = (
                f"bestvideo[height<={height}][ext={video_format}]+bestaudio/"
                f"bestvideo[height<={height}]+bestaudio/best[ext={video_format}]/"
                f"bestvideo[height<={height}]+bestaudio/best"
            )
            ydl_opts["postprocessors"] = [{
                "key": "FFmpegVideoConvertor",
                "preferedformat": video_format,
            }]

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            if self.cancel_event.is_set():
                self.after(0, lambda: self.on_download_complete(False, "Download cancelled."))
            else:
                self.after(0, lambda: self.on_download_complete(True, "Download complete!"))
        except yt_dlp.utils.DownloadError as e:
            error_msg: str = str(e)
            if self.cancel_event.is_set():
                self.after(0, lambda: self.on_download_complete(False, "Download cancelled."))
            elif "HTTP Error 429" in error_msg:
                self.after(0, lambda: self.on_download_complete(
                    False, "Rate limited by YouTube. Please wait a few minutes and try again."
                ))
            elif "Video unavailable" in error_msg or "geographic" in error_msg.lower():
                self.after(0, lambda: self.on_download_complete(
                    False, "Video unavailable in your region. Try using a proxy or VPN."
                ))
            elif "age" in error_msg.lower() or "age-restricted" in error_msg.lower():
                self.after(0, lambda: self.on_download_complete(
                    False, "Video is age-restricted."
                ))
            else:
                self.after(0, lambda m=error_msg: self.on_download_complete(
                    False, f"Download error: {m}"
                ))
        except Exception as e:
            self.after(0, lambda m=str(e): self.on_download_complete(False, f"Error: {m}"))

    def my_hook(self, d: dict) -> None:
        if self.cancel_event.is_set() and d.get("status") == "downloading":
            raise Exception("Download cancelled by user.")

        if d["status"] == "downloading":
            percent: float = self._calculate_progress(d)
            self.after(0, lambda p=percent: self.progress_bar.set(p))
            self.after(0, lambda: self.status_label.configure(
                text=f"Downloading... {d.get('_percent_str', '0%')} (ETA: {d.get('_eta_str','?')})"
            ))
        elif d["status"] == "finished":
            self.after(0, lambda: self.progress_bar.set(1))
            self.after(0, lambda: self.status_label.configure(text="Processing..."))
        elif d["status"] == "error":
            self.after(0, lambda: self.status_label.configure(text="Error during download"))

    def _calculate_progress(self, d: dict) -> float:
        if d.get("_percent_str"):
            try:
                return float(d["_percent_str"].replace("%", "").strip()) / 100.0
            except (ValueError, AttributeError):
                pass
        downloaded: Optional[int] = d.get("downloaded_bytes")
        total: Optional[int] = d.get("total_bytes") or d.get("total_bytes_estimate")
        if downloaded and total and total > 0:
            try:
                return downloaded / total
            except (TypeError, ZeroDivisionError):
                pass
        return 0.0

    def on_download_complete(self, success: bool, message: str) -> None:
        self.is_downloading = False
        if success:
            self.progress_bar.set(1)
            self.status_label.configure(text=message)
        else:
            self.progress_bar.set(0)
            self.status_label.configure(text=message)
        self.download_btn.configure(state="normal")
        self.cancel_btn.configure(state="disabled")


if __name__ == "__main__":
    app = YTDLPDownloader()
    app.mainloop()
