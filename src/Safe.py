"""
    Safe.py - Simple utility helpers for the YoutubeDownloader.
    Handles filename sanitization and FFmpeg binary resolution.
    Kept free of any Streamlit imports so it can be reused outside the UI.
    Author: Mohammad Javad Majlesi
"""

import re
import os
import shutil


def safe_filename(name: str) -> str:
    """حذف کاراکترهای غیرمجاز از اسم فایل برای ویندوز"""
    return re.sub(r'[<>:"/\\|?*]', '_', name)


def get_ffmpeg_path() -> str:
    """
    Resolves an FFmpeg executable path.
    Tries the system PATH first, then falls back to the bundled
    imageio-ffmpeg binary so the app works even when FFmpeg is not
    installed globally.
    :return: Path to an FFmpeg executable, or None if not found.
    """
    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        return system_ffmpeg

    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except (ImportError, Exception):
        return None


def has_ffmpeg() -> bool:
    """Returns True if an FFmpeg executable is available."""
    return get_ffmpeg_path() is not None