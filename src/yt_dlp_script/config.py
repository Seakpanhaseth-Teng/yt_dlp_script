import os
from pathlib import Path

VERSION: str = "1.0.0"

# Colors
PRIMARY_COLOR: str = "#1AABFF"
BG_COLOR: str = "#000000"
HOVER_COLOR: str = "#B20000"
UPDATE_BTN_COLOR: str = "#444444"
CANCEL_BTN_COLOR: str = "#CC3333"
CANCEL_BTN_TEXT_COLOR: str = "#FFFFFF"

# Dimensions
WINDOW_GEOMETRY: str = "550x520"
WINDOW_RESIZABLE: tuple[bool, bool] = (True, True)
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
PAD_X_DEFAULT: int = 5
PAD_X_LABEL: tuple[int, int] = (10, 5)
PAD_X_FRAME: int = 10
PAD_X_RES: int = 5
PAD_X_BROWSE: int = 5
PAD_X_SSL: int = 10
PAD_X_BUTTON: int = 10

# Fonts
FONT_NAME: str = "Segoe UI"
FONT_SIZE: int = 13
FONT_BOLD_SIZE: int = 15
FONT: tuple[str, int] = (FONT_NAME, FONT_SIZE)
FONT_BOLD: tuple[str, int, str] = (FONT_NAME, FONT_BOLD_SIZE, "bold")

# Timeouts
PIP_TIMEOUT: int = 300
PYPI_TIMEOUT: int = 5

# Download settings
DEFAULT_RESOLUTION: str = "1080p"
DEFAULT_AUDIO: str = "None"
DEFAULT_VIDEO_FORMAT: str = "mp4"
DEFAULT_AUDIO_QUALITY: str = "192"
MAX_RETRIES: int = 5
MAX_FRAGMENT_RETRIES: int = 5
NO_PLAYLIST: bool = True
PLAYLIST_DEFAULT: bool = False

# URLs
PYPI_API_URL: str = "https://pypi.org/pypi/yt-dlp/json"

# FFmpeg
FFMPEG_EXECUTABLE: str = os.environ.get("YTDLP_FFMPEG_EXECUTABLE", "ffmpeg.exe")
_SCRIPT_DIR: Path = Path(__file__).resolve().parent
PROJECT_ROOT: Path = _SCRIPT_DIR.parent.parent
