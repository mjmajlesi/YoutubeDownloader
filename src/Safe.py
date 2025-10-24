from pytubefix import YouTube
from urllib.error import URLError
import re, time
# DO NOT import streamlit here. Keep utils separate from the UI.

# This is the correct way to patch the default_range_size
from pytubefix import request
request.default_range_size = 1048576  # 1MB chunk size

def safe_filename(name: str) -> str:
    """حذف کاراکترهای غیرمجاز از اسم فایل برای ویندوز"""
    return re.sub(r'[<>:"/\\|?*]', '_', name)

def safe_youtube(url, retries=3, delay=3):
    """
    Tries to get a YouTube object, retrying on URLError.
    Raises an exception if it fails after all retries.
    """
    last_exception = None
    for i in range(retries):
        try:
            return YouTube(
                url,
                on_progress_callback=None,
                on_complete_callback=None
            )
        except URLError as e:
            print(f"Connection error: {e}, retrying {i+1}/{retries} ...")
            last_exception = e
            time.sleep(delay)
            
    # If loop finishes without returning, raise the last error
    raise Exception(f"❌ Failed to connect after {retries} retries. Error: {last_exception}")

def is_playlist_url(url: str) -> bool:
    """Quick check to see if the provided URL is a YouTube playlist URL."""
    if not isinstance(url, str):
        return False
    # common patterns for YouTube playlists: 'list=' param or '/playlist?'
    return 'list=' in url or '/playlist' in url