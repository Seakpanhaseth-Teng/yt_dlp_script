# Project: yt_dlp_script

## Goal
Transform a monolithic YouTube downloader script into a modular, industry-standard Python project with clean architecture, tests, type checking, CI, and professional tooling. All code must demonstrate clean practices for employer showcase.

## Execution Preferences
- Write tests for every code change; use `pytest -v --cov=yt_dlp_script` and `python -m mypy src/ tests/` to verify.
- Ruff is locally blocked (Win policy); CI runs it on Ubuntu. Use `mypy` and `pytest` locally.
- Package is installed in editable mode via `pip install -e .`.
- Python 3.11.9, customtkinter 5.2.2, yt-dlp 2026.3.17.
- Tests use mock strategy: bypass `__init__`, wire MagicMock widgets (see `tests/conftest.py`).

## Recent Work (Sessions 1-2)

### Session 1 — Initial Restructure
- Monolithic `downloader.py` → `src/yt_dlp_script/` package: `config.py`, `exceptions.py`, `utils.py`, `downloader.py`, `gui.py`, `__init__.py`, `__main__.py`.
- Fixed `PAD_X_DEFAULT` NameError bug (missing constant in `config.py`).
- Renamed `my_hook` → `_progress_hook`; dead code `check_for_updates()` removed.
- Separated `DownloadManager` (business logic) from `YTDLPDownloader` (GUI).
- Custom exceptions: `YTDLPError`, `ValidationError`, `FolderNotFoundError`, `FolderNotWritableError`, `DownloadCancelledError`.
- URL regex expanded with `music.`/`m.` subdomains, `/live/`, extra params.
- Cross-platform `outtmpl` via `Path(folder) / "%(title)s.%(ext)s"`.
- Fixed false completed-as-cancelled: removed `cancel_event.is_set()` check after successful download.
- Professional tooling: `pyproject.toml`, `requirements.txt`, `requirements-dev.txt`, `Makefile`, `.pre-commit-config.yaml`, `.github/workflows/ci.yml`, `LICENSE`.
- 89 tests across `test_utils.py`, `test_downloader.py`, `test_gui.py`.

### Session 2 — Playlist + Code Quality
- **Playlist support**: Added "Download entire playlist" checkbox. `build_options()` accepts `playlist=False` param; sets `noplaylist` and `ignoreerrors`. Threaded through GUI → manager. Test count: 90.
- **Fixed mypy**: Collection.abc `Iterator` for generator fixtures; `TYPE_CHECKING` import in conftest.
- **Refactored `_create_widgets`** (200-line monolith → 7 focused methods: `_create_url_section`, `_create_folder_section`, `_create_options_section`, `_create_checkboxes`, `_create_update_button`, `_create_action_buttons`, `_create_status_section`).
- **Removed dead imports** in `main()` (`logging`, `sys` — already at top level; added `sys` to top).
- **Fixed Makefile**: Cross-platform `clean` target (`$(OS)` conditional); `ci` now includes `format-check`.
- **Fixed critical issues**:
  - `get_current_version()`: `except PackageNotFoundError` instead of bare `Exception`.
  - `fetch_latest_version()`: `except (URLError, JSONDecodeError, KeyError)` instead of bare `Exception`.
  - `update_yt_dlp()`: venv guard (`sys.prefix != sys.base_prefix`) + specific `except` clauses (`TimeoutExpired`, `CalledProcessError`, `OSError`).
- **Added 3 new tests**: `test_update_no_venv_returns_warning`, `test_update_timeout`, `test_update_os_error`. Total: 93 tests (utils coverage 99%).

## Next Steps (Highest Impact First)

1. **Download queue** — multiple URL input, sequential processing, job tracking (queued → downloading → done/failed).
2. **Graceful window-close handling** — prevent `TclError` from daemon threads when window closed mid-download.
3. **File logging** — persistent download history to `yt_dlp_script.log`.
4. **PyInstaller `.exe`** — standalone distribution without Python.
5. **Pre-commit hooks** — run `pre-commit install`.
6. **CI badge** in README — once CI runs on GitHub.

## Project Layout
```
src/yt_dlp_script/
├── __init__.py          # Package marker
├── __main__.py          # Entry point
├── config.py            # Constants, colors, dimensions, defaults
├── exceptions.py        # Custom exception classes
├── utils.py             # Validation, FFmpeg detection, version helpers, ETA
├── downloader.py        # DownloadManager — download orchestration
└── gui.py               # YTDLPDownloader — CustomTkinter GUI
tests/
├── conftest.py          # Fixture: bypass __init__, mock widgets
├── test_utils.py        # 36 tests
├── test_downloader.py   # 23 tests
└── test_gui.py          # 34 tests (no display required)
```

## Key Architectural Decisions
- `noplaylist: True` is default (checkbox to enable). Prevents accidental full-playlist downloads.
- GUI tests mock widgets: `__init__` patched, object via `__new__`, all widget attrs as `MagicMock`. Headless CI works.
- Download cancellation is best-effort (works during progress hook callbacks only).
- No `.env` support (no `python-dotenv` dep needed). FFmpeg overridable via `YTDLP_FFMPEG_EXECUTABLE` env var.
- `update_yt_dlp()` refuses to run outside a virtual environment.

## Commands
```bash
pytest -v --cov=yt_dlp_script          # Run all tests
python -m mypy src/ tests/              # Type check
make test                               # Tests
make lint                               # Ruff lint
make typecheck                          # mypy
make ci                                 # Full CI pipeline (lint + format-check + typecheck + test)
```

## Git Status
All changes are uncommitted. Modified: `.gitignore`, `README.md`, `requirements.txt`. Deleted: `downloader.py`. New untracked: `.github/`, `.pre-commit-config.yaml`, `LICENSE`, `Makefile`, `pyproject.toml`, `requirements-dev.txt`, `src/`, `tests/`, `AGENTS.md`.
