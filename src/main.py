from pytubefix import YouTube
from pathlib import Path
import streamlit as st
import subprocess
import os, re, time
from urllib.error import URLError

def safe_filename(name: str) -> str:
    """حذف کاراکترهای غیرمجاز از اسم فایل برای ویندوز"""
    return re.sub(r'[<>:"/\\|?*]', '_', name)

def safe_youtube(url, retries=3, delay=3):
    """Retry wrapper برای یوتیوب وقتی connection قطع بشه"""
    for i in range(retries):
        try:
            return YouTube(
                url,
                on_progress_callback=None,  # بعدا ست می‌کنیم
                on_complete_callback=None
            )
        except URLError as e:
            st.warning(f"⚠️ Connection error: {e}, retrying {i+1}/{retries} ...")
            time.sleep(delay)
    raise Exception("❌ Failed to connect after multiple retries.")


class YoutubeDownloader:
    def __init__(self, url, Only_audio=False, path_output=None, quality=None):
        self.url = url
        self.Only_audio = Only_audio
        self.path_output = path_output or Path().cwd()
        self.quality = quality or "highest"

        self.progress_bar = st.progress(0)
        self.last_percent = 0

        # یوتیوب با retry
        self.yt = safe_youtube(self.url)
        # وصل کردن callbacks بعد از ساخت
        self.yt.register_on_progress_callback(self.on_progress)
        self.yt.register_on_complete_callback(self.on_completed)

    def Download(self):
        if self.Only_audio:
            stream = self.yt.streams.filter(only_audio=True).first()
            if not stream:
                st.error("❌ No audio stream found.")
                return None
            return stream.download(output_path=self.path_output)

        # --- انتخاب استریم ---
        if self.quality == "highest":
            stream = self.yt.streams.get_highest_resolution()
        else:
            stream = self.yt.streams.filter(progressive=True, res=self.quality, file_extension="mp4").first()

        # اگه progressive نبود، adaptive رو می‌گیریم
        if stream is None:
            video_stream = self.yt.streams.filter(adaptive=True, res=self.quality, mime_type="video/mp4").first()
            audio_stream = self.yt.streams.filter(adaptive=True, mime_type="audio/mp4").order_by("abr").desc().first()
            if not video_stream or not audio_stream:
                st.error(f"❌ No stream found for quality {self.quality}")
                return None

            video_path = video_stream.download(output_path=self.path_output, filename="temp_video.mp4")
            audio_path = audio_stream.download(output_path=self.path_output, filename="temp_audio.mp4")

            filename = safe_filename(f"{self.yt.title}_{self.quality}.mp4")
            output_path = os.path.join(self.path_output, filename)

            # --- merge با ffmpeg ---
            cmd = [
                "ffmpeg", "-y",
                "-i", video_path,
                "-i", audio_path,
                "-c", "copy",
                output_path
            ]
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            os.remove(video_path)
            os.remove(audio_path)
            return output_path

        # اگه progressive بود → مستقیم دانلود
        else:
            filename = safe_filename(f"{self.yt.title}_{self.quality}.mp4")
            return stream.download(output_path=self.path_output, filename=filename)

    def on_progress(self, stream, chunk, bytes_remaining):
        total = getattr(stream, 'filesize', None) or getattr(stream, 'filesize_approx', 0)
        downloaded = total - bytes_remaining
        percent = int(downloaded / total * 100)
        if percent > self.last_percent:
            self.progress_bar.progress(percent)
            self.last_percent = percent

    def on_completed(self, stream, file_path):
        st.success("✅ Download completed!")
