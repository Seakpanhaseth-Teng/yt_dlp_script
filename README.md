# YouTube Downloader (yt-dlp Wrapper)

A modern GUI application for downloading YouTube videos and audio, built with
CustomTkinter and yt-dlp.

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![yt-dlp](https://img.shields.io/badge/yt--dlp-latest-red.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## Features

- **Video Download** – Download YouTube videos in multiple resolutions (360p to 4K)
- **Audio Extraction** – Extract audio as MP3, M4A, or WAV
- **Format Conversion** – Convert videos to MP4, MKV, WebM, MOV, AVI, or FLV
- **Auto-Update** – Keep yt-dlp updated with one click
- **Progress Tracking** – Real-time download progress with ETA
- **Download Cancellation** – Cancel downloads in progress
- **Playlist Support** – Optionally download entire YouTube playlists
- **URL Validation** – Validates YouTube URLs before downloading
- **Smart FFmpeg Detection** – Automatically detects bundled or system FFmpeg

## Prerequisites

- Python 3.10 or higher
- Windows 10/11 (Linux/macOS support requires system FFmpeg)

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/yt_dlp_script.git
cd yt_dlp_script
```

### 2. Create a Virtual Environment

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -e .
```

### 4. (Optional) Install Development Dependencies

```bash
pip install -r requirements-dev.txt
```

### 5. FFmpeg

FFmpeg is bundled with this project for Windows users. If you're on Linux or
macOS, install FFmpeg:

```bash
# Ubuntu/Debian
sudo apt install ffmpeg

# macOS
brew install ffmpeg
```

## Usage

### Running the Application

```bash
# Via installed script
yt-dlp-downloader

# Or via Python module
python -m yt_dlp_script

# Or directly (after pip install -e .)
python src/yt_dlp_script/__main__.py
```

### How to Download

1. **Paste a YouTube URL** – Enter a valid YouTube video, short, or playlist URL
2. **Select Save Folder** – Choose where to save the file (defaults to Downloads)
3. **Choose Resolution** – Select desired video quality
4. **Choose Audio Format** (optional) – Select MP3, M4A, or WAV to extract audio only
5. **Choose Video Format** – Select output format (MP4, MKV, WebM, MOV, AVI, FLV)
6. **Toggle Playlist** (optional) – Check "Download entire playlist" to download all videos
7. **Click Start Download** – Or press Enter in the URL field

### Options

| Option         | Description                                                    |
|----------------|----------------------------------------------------------------|
| **Resolution** | Maximum video resolution (applies to video downloads only)      |
| **Audio**      | Extract audio only (selecting disables video download)          |
| **Format**     | Output video container format                                   |
| **SSL Bypass** | Disable SSL certificate verification (not recommended)          |
| **Playlist**   | Download all videos in a playlist instead of the first one only |

## Project Structure

```
yt_dlp_script/
├── src/
│   └── yt_dlp_script/            # Main Python package
│       ├── __init__.py            # Package metadata
│       ├── __main__.py            # Entry point (`python -m yt_dlp_script`)
│       ├── config.py              # Constants, colors, dimensions, defaults
│       ├── exceptions.py          # Custom exception classes
│       ├── utils.py               # Validation, FFmpeg detection, version helpers
│       ├── downloader.py          # DownloadManager – download orchestration
│       └── gui.py                 # YTDLPDownloader – CustomTkinter GUI
├── tests/                         # Test suite (pytest)
│   ├── __init__.py
│   ├── test_utils.py              # Unit tests for utility functions
│   └── test_downloader.py         # Unit tests for download logic
├── pyproject.toml                 # Project configuration & tooling
├── requirements.txt               # Runtime dependencies
├── requirements-dev.txt           # Development dependencies
├── Makefile                       # Common commands (test, lint, format...)
├── .pre-commit-config.yaml        # Pre-commit hooks (ruff, mypy)
├── .github/workflows/ci.yml       # GitHub Actions CI pipeline
├── LICENSE                        # MIT License
├── README.md                      # This file
└── .gitignore
```

## Development

### Running Tests

```bash
pytest -v --cov=yt_dlp_script
```

### Linting & Formatting

```bash
# Lint
ruff check src/ tests/

# Format
ruff format src/ tests/

# Type check
mypy src/
```

### Pre-commit Hooks

```bash
pip install pre-commit
pre-commit install
```

## Supported URL Formats

- `https://www.youtube.com/watch?v=VIDEO_ID`
- `https://youtu.be/VIDEO_ID`
- `https://www.youtube.com/shorts/VIDEO_ID`
- `https://www.youtube.com/embed/VIDEO_ID`
- `https://www.youtube.com/playlist?list=PLAYLIST_ID`

## Troubleshooting

### "Video unavailable" Error

- The video may be private, deleted, or geo-restricted
- Try using a VPN or enabling the SSL bypass option

### "HTTP Error 429" (Rate Limited)

- YouTube has temporarily blocked your IP
- Wait a few minutes and try again

### "ffmpeg not found" Warning

- Video merging and audio extraction may fail without FFmpeg
- Ensure the `ffmpeg-master-latest-win64-gpl` folder exists, or install FFmpeg
  system-wide

### Download Stuck at 0%

- Check your internet connection
- The video may have restricted downloads enabled

## Dependencies

| Package         | Version | Purpose                        |
|-----------------|---------|--------------------------------|
| customtkinter   | 5.2+    | Modern GUI framework            |
| yt-dlp          | Latest  | Video/audio downloader          |
| darkdetect      | Auto    | Theme detection (transitive)    |

## License

MIT License – see [LICENSE](LICENSE) for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request
