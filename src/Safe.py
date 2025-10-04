from pytubefix import YouTube
from urllib.error import URLError
import re, time
import streamlit as st

def safe_filename(name: str) -> str:
    """حذف کاراکترهای غیرمجاز از اسم فایل برای ویندوز"""
    return re.sub(r'[<>:"/\\|?*]', '_', name)

def safe_youtube(url, retries=3, delay=3):
    for i in range(retries):
        try:
            return YouTube(
                url,
                on_progress_callback=None,
                on_complete_callback=None
            )
        except URLError as e:
            st.warning(f"⚠️ Connection error: {e}, retrying {i+1}/{retries} ...")
            time.sleep(delay)
    raise Exception("❌ Failed to connect after multiple retries.")

def is_playlist_url(url: str) -> bool:
    """Quick check to see if the provided URL is a YouTube playlist URL."""
    if not isinstance(url, str):
        return False
    # common patterns for YouTube playlists: 'list=' param or '/playlist?'
    return 'list=' in url or '/playlist' in url