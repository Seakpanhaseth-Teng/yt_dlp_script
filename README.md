# YouTube Downloader (yt-dlp Wrapper)

A modern GUI application for downloading YouTube videos and audio, built with CustomTkinter and yt-dlp.

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![yt-dlp](https://img.shields.io/badge/yt--dlp-latest-red.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## Features

- **Video Download** - Download YouTube videos in multiple resolutions (360p to 4K)
- **Audio Extraction** - Extract audio as MP3, M4A, or WAV
- **Format Conversion** - Convert videos to MP4, MKV, WebM, MOV, AVI, or FLV
- **Auto-Update** - Keep yt-dlp updated with one click
- **Progress Tracking** - Real-time download progress with ETA
- **Download Cancellation** - Cancel downloads in progress
- **URL Validation** - Validates YouTube URLs before downloading
- **Smart FFmpeg Detection** - Automatically detects bundled or system FFmpeg

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
.venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. FFmpeg

FFmpeg is bundled with this project for Windows users. If you're on Linux or macOS, install FFmpeg:

```bash
# Ubuntu/Debian
sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Windows (optional, if bundled version doesn't work)
winget install ffmpeg
```

## Usage

### Running the Application

```bash
python downloader.py
```

### How to Download

1. **Paste a YouTube URL** - Enter a valid YouTube video, short, or playlist URL
2. **Select Save Folder** - Choose where to save the file (defaults to Downloads)
3. **Choose Resolution** - Select desired video quality (360p, 480p, 720p, 1080p, 1440p, 2160p)
4. **Choose Audio Format** (optional) - Select MP3, M4A, or WAV to extract audio only
5. **Choose Video Format** - Select output format (MP4, MKV, WebM, MOV, AVI, FLV)
6. **Click Start Download** - Or press Enter in the URL field

### Options

| Option | Description |
|--------|-------------|
| **Resolution** | Maximum video resolution (applies to video downloads only) |
| **Audio** | Extract audio only (selecting an audio format disables video download) |
| **Format** | Output video container format |
| **SSL Bypass** | Disable SSL certificate verification (not recommended, use only for network issues) |

## Project Structure

```
yt_dlp_script/
├── downloader.py              # Main application
├── requirements.txt           # Python dependencies
├── .gitignore                 # Git ignore rules
├── .venv/                     # Python virtual environment
└── ffmpeg-master-latest-win64-gpl/  # Bundled FFmpeg (Windows)
```

## Supported URL Formats

- `https://www.youtube.com/watch?v=VIDEO_ID`
- `https://youtu.be/VIDEO_ID`
- `https://www.youtube.com/shorts/VIDEO_ID`
- `https://www.youtube.com/embed/VIDEO_ID`
- `https://www.youtube.com/playlist?list=PLAYLIST_ID` (video downloads only)

## Troubleshooting

### "Video unavailable" Error
- The video may be private, deleted, or geo-restricted
- Try using a VPN or enabling the SSL bypass option

### "HTTP Error 429" (Rate Limited)
- YouTube has temporarily blocked your IP
- Wait a few minutes and try again

### "ffmpeg not found" Warning
- Video merging and audio extraction may fail without FFmpeg
- Ensure the `ffmpeg-master-latest-win64-gpl` folder exists, or install FFmpeg system-wide

### Download Stuck at 0%
- Check your internet connection
- The video may have restricted downloads enabled

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| customtkinter | 5.2+ | Modern GUI framework |
| yt-dlp | Latest | Video/audio downloader |
| darkdetect | Auto | Theme detection |

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request
