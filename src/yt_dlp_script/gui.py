import logging
import os
import sys
import threading
from pathlib import Path
from typing import Any, Optional

import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox

from yt_dlp_script.config import (
    BG_COLOR,
    BUTTON_HEIGHT_LARGE,
    BUTTON_HEIGHT_SMALL,
    BUTTON_WIDTH_CANCEL,
    BUTTON_WIDTH_DOWNLOAD,
    BUTTON_WIDTH_UPDATE,
    CANCEL_BTN_COLOR,
    CANCEL_BTN_TEXT_COLOR,
    DEFAULT_AUDIO,
    DEFAULT_RESOLUTION,
    DEFAULT_VIDEO_FORMAT,
    ENTRY_WIDTH_FOLDER,
    ENTRY_WIDTH_MAIN,
    FONT,
    FONT_BOLD,
    FRAME_PADX,
    HOVER_COLOR,
    PAD_X_BROWSE,
    PAD_X_BUTTON,
    PAD_X_DEFAULT,
    PAD_X_FRAME,
    PAD_X_LABEL,
    PAD_X_RES,
    PAD_X_SSL,
    PAD_Y_BUTTON,
    PAD_Y_DEFAULT,
    PAD_Y_PROGRESS,
    PAD_Y_SSL,
    PAD_Y_STATUS,
    PAD_Y_TOP,
    PAD_Y_UPDATE,
    PLAYLIST_DEFAULT,
    PRIMARY_COLOR,
    PROGRESS_BAR_HEIGHT,
    PROGRESS_BAR_WIDTH,
    UPDATE_BTN_COLOR,
    WINDOW_GEOMETRY,
    WINDOW_RESIZABLE,
    WRAP_LENGTH,
)
from yt_dlp_script.downloader import DownloadManager, DownloadResult
from yt_dlp_script.exceptions import (
    FolderNotFoundError,
    ValidationError,
)
from yt_dlp_script.utils import (
    fetch_latest_version,
    format_eta,
    get_current_version,
    update_yt_dlp,
    validate_folder,
    validate_url,
)

logger = logging.getLogger(__name__)


class YTDLPDownloader(ctk.CTk):  # type: ignore[misc]  # customtkinter stubs are incomplete
    def __init__(self) -> None:
        super().__init__()
        self.title("YouTube Downloader (yt-dlp Wrapper)")
        self.geometry(WINDOW_GEOMETRY)
        self.resizable(*WINDOW_RESIZABLE)
        self.configure(bg=BG_COLOR)

        self.manager = DownloadManager()

        self.url_var: tk.StringVar = tk.StringVar()
        self.folder_var: tk.StringVar = tk.StringVar(
            value=str(Path.home() / "Downloads")
        )
        self.resolution_var: tk.StringVar = tk.StringVar(value=DEFAULT_RESOLUTION)
        self.audio_var: tk.StringVar = tk.StringVar(value=DEFAULT_AUDIO)
        self.video_format_var: tk.StringVar = tk.StringVar(
            value=DEFAULT_VIDEO_FORMAT
        )
        self.ssl_bypass_var: tk.BooleanVar = tk.BooleanVar(value=False)
        self.playlist_var: tk.BooleanVar = tk.BooleanVar(value=PLAYLIST_DEFAULT)

        self.manager.on_progress(self._on_progress_hook)

        self._create_widgets()
        threading.Thread(target=self._check_version_worker, daemon=True).start()

    # ── Widget creation ────────────────────────────────────────────────────────

    def _create_widgets(self) -> None:
        self._create_url_section()
        self._create_folder_section()
        self._create_options_section()
        self._create_checkboxes()
        self._create_update_button()
        self._create_action_buttons()
        self._create_status_section()

    def _create_url_section(self) -> None:
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
        self.url_entry.bind("<Return>", lambda _: self.start_download())

    def _create_folder_section(self) -> None:
        self.folder_frame = ctk.CTkFrame(self, fg_color=BG_COLOR)
        self.folder_frame.pack(pady=PAD_Y_DEFAULT, fill="x", padx=FRAME_PADX)

        self.folder_label = ctk.CTkLabel(
            self.folder_frame,
            text="Save Folder:",
            font=FONT,
            text_color=PRIMARY_COLOR,
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

    def _create_options_section(self) -> None:
        self.options_frame = ctk.CTkFrame(self, fg_color=BG_COLOR)
        self.options_frame.pack(pady=PAD_Y_DEFAULT, fill="x", padx=FRAME_PADX)

        self.resolution_frame = ctk.CTkFrame(self.options_frame, fg_color=BG_COLOR)
        self.resolution_frame.pack(side="left", padx=PAD_X_RES)

        self.res_label = ctk.CTkLabel(
            self.resolution_frame,
            text="Resolution:",
            font=FONT,
            text_color=PRIMARY_COLOR,
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
            self.format_frame,
            text="Format:",
            font=FONT,
            text_color=PRIMARY_COLOR,
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

    def _create_checkboxes(self) -> None:
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

        self.playlist_checkbox = ctk.CTkCheckBox(
            self.ssl_frame,
            text="Download entire playlist",
            variable=self.playlist_var,
            text_color=PRIMARY_COLOR,
            font=FONT,
            fg_color=BG_COLOR,
            border_color=PRIMARY_COLOR,
        )
        self.playlist_checkbox.pack(side="left", padx=PAD_X_SSL)

    def _create_update_button(self) -> None:
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

    def _create_action_buttons(self) -> None:
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

    def _create_status_section(self) -> None:
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

    # ── Version check ──────────────────────────────────────────────────────────

    def _check_version_worker(self) -> None:
        current: Optional[str] = get_current_version()
        latest: Optional[str] = fetch_latest_version()
        self.after(0, lambda: self._on_version_check(current, latest))

    def _on_version_check(
        self, current: Optional[str], latest: Optional[str]
    ) -> None:
        if current is None:
            self.status_label.configure(text="Could not detect yt-dlp version")
            return
        if latest and latest != current:
            self.status_label.configure(
                text=f"Update available: {current} to {latest}"
            )
        else:
            self.status_label.configure(text="yt-dlp is up to date")

    def do_update(self) -> None:
        self.status_label.configure(text="Updating yt-dlp...")
        self.update_btn.configure(state="disabled")
        threading.Thread(target=self._update_thread, daemon=True).start()

    def _update_thread(self) -> None:
        result: str = update_yt_dlp()
        self.after(0, lambda: self._on_update_result(result))

    def _on_update_result(self, message: str) -> None:
        self.status_label.configure(text=message)
        self.update_btn.configure(state="normal")

    # ── Download flow ──────────────────────────────────────────────────────────

    def browse_folder(self) -> None:
        folder_selected: str = filedialog.askdirectory()
        if folder_selected:
            self.folder_var.set(folder_selected)

    def start_download(self) -> None:
        if self.manager.is_downloading:
            logger.warning("Download already in progress.")
            return

        url: str = self.url_var.get().strip()
        folder: str = self.folder_var.get().strip()
        resolution: str = self.resolution_var.get()
        audio_format: str = self.audio_var.get()
        video_format: str = self.video_format_var.get()
        ssl_bypass: bool = self.ssl_bypass_var.get()
        playlist: bool = self.playlist_var.get()

        try:
            validate_url(url)
        except ValidationError as e:
            messagebox.showerror("Error", str(e))
            return

        try:
            validate_folder(folder)
        except FolderNotFoundError:
            response = messagebox.askyesno(
                "Folder Not Found",
                f"The folder '{folder}' does not exist.\n"
                "Would you like to create it?",
            )
            if response:
                try:
                    Path(folder).mkdir(parents=True, exist_ok=True)
                    logger.info("Created folder: %s", folder)
                    if not os.access(folder, os.W_OK):
                        messagebox.showerror(
                            "Error",
                            f"Created folder '{folder}' but it is not writable.",
                        )
                        return
                except OSError as e:
                    messagebox.showerror("Error", f"Failed to create folder: {e}")
                    return
            else:
                messagebox.showerror("Error", "Folder does not exist.")
                return
        except ValidationError as e:
            messagebox.showerror("Error", str(e))
            return

        if not self.manager.ffmpeg_dir:
            messagebox.showwarning(
                "FFmpeg Not Found",
                "ffmpeg was not found. "
                "Video merging and audio extraction may fail.",
            )

        self.manager.reset()
        self.status_label.configure(text="Downloading...")
        self.download_btn.configure(state="disabled")
        self.cancel_btn.configure(state="normal")
        self.progress_bar.set(0)

        threading.Thread(
            target=self._run_download,
            args=(url, folder, resolution, audio_format, video_format, ssl_bypass, playlist),
            daemon=True,
        ).start()

    def _run_download(
        self,
        url: str,
        folder: str,
        resolution: str,
        audio_format: str,
        video_format: str,
        ssl_bypass: bool,
        playlist: bool = False,
    ) -> None:
        result = self.manager.download(
            url=url,
            folder=folder,
            resolution=resolution,
            audio_format=audio_format,
            video_format=video_format,
            ssl_bypass=ssl_bypass,
            playlist=playlist,
        )
        self.after(0, lambda r=result: self._on_download_complete(r))

    def cancel_download(self) -> None:
        self.manager.cancel()
        self.status_label.configure(text="Cancelling...")

    def _on_progress_hook(self, data: dict[str, Any]) -> None:
        status: str = data.get("status", "")

        if status == "downloading":
            percent: float = self.manager.calculate_progress(data)
            self.after(0, lambda p=percent: self.progress_bar.set(p))
            eta: str = format_eta(data)
            self.after(
                0,
                lambda d=data, e=eta: self.status_label.configure(
                    text=(
                        f"Downloading... {d.get('_percent_str', '0%')} "
                        f"(ETA: {e})"
                    )
                ),
            )
        elif status == "finished":
            self.after(0, lambda: self.progress_bar.set(1))
            self.after(
                0,
                lambda: self.status_label.configure(text="Processing..."),
            )
        elif status == "error":
            self.after(
                0,
                lambda: self.status_label.configure(
                    text="Error during download"
                ),
            )

    def _on_download_complete(self, result: DownloadResult) -> None:
        if result.success:
            self.progress_bar.set(1)
        else:
            self.progress_bar.set(0)
            messagebox.showerror("Download Failed", result.message)
        self.status_label.configure(text=result.message)
        self.download_btn.configure(state="normal")
        self.cancel_btn.configure(state="disabled")


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("dark-blue")

    app = YTDLPDownloader()
    app.mainloop()
