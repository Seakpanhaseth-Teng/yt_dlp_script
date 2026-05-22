class YTDLPError(Exception):
    """Base exception for the yt-dlp downloader application."""


class ValidationError(YTDLPError):
    """Raised when user input fails validation."""


class FolderNotFoundError(ValidationError):
    """Raised when the specified save folder does not exist."""


class FolderNotWritableError(ValidationError):
    """Raised when the specified save folder is not writable."""


class DownloadCancelledError(YTDLPError):
    """Raised when the user cancels an active download."""
