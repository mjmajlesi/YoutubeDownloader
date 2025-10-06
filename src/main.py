from pytubefix import YouTube, Playlist
import streamlit as st
import subprocess
import os, re, time, io
from urllib.error import URLError
from src.Safe import safe_filename, safe_youtube, is_playlist_url

class YoutubeDownloader:
    def __init__(self, url, Only_audio=False, quality=None):
        self.url = url
        self.Only_audio = Only_audio
        self.quality = quality or "highest"
        self.progress_bar = st.progress(0)
        self.last_percent = 0

        # تشخیص نوع URL (playlist یا video)
        self.is_playlist = is_playlist_url(self.url)
        self.yt = None
        self.pl = None
        if self.is_playlist:
            try:
                self.pl = Playlist(self.url)
            except Exception:
                self.pl = None
        else:
            self.yt = safe_youtube(self.url)
            self.yt.register_on_progress_callback(self.on_progress)
            self.yt.register_on_complete_callback(self.on_completed)

    # ---------------------- VIDEO ----------------------
    def Download(self):
        if not self.yt:
            st.error("❌ No video object available to download.")
            return None

        if self.quality == "highest":
            stream = self.yt.streams.get_highest_resolution()
        else:
            stream = self.yt.streams.filter(progressive=True, res=self.quality, file_extension="mp4").first()

        # adaptive case (video + audio merge)
        if stream is None:
            video_stream = self.yt.streams.filter(adaptive=True, res=self.quality, mime_type="video/mp4").first()
            audio_stream = self.yt.streams.filter(adaptive=True, mime_type="audio/mp4").order_by("abr").desc().first()
            if not video_stream or not audio_stream:
                st.error(f"❌ No stream found for quality {self.quality}")
                return None

            # دانلود به فایل موقت
            video_path = video_stream.download(filename="temp_video.mp4")
            audio_path = audio_stream.download(filename="temp_audio.mp4")
            output_path = "merged_temp.mp4"

            cmd = [
                "ffmpeg", "-y",
                "-i", video_path,
                "-i", audio_path,
                "-c", "copy",
                output_path
            ]
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            # خواندن به حافظه
            with open(output_path, "rb") as f:
                file_data = f.read()

            # پاکسازی فایل‌ها
            for f in [video_path, audio_path, output_path]:
                try:
                    os.remove(f)
                except:
                    pass

            # بازگشت داده به صورت BytesIO
            buffer = io.BytesIO(file_data)
            buffer.seek(0)
            return buffer

        # progressive case
        else:
            buffer = io.BytesIO()
            stream.stream_to_buffer(buffer)
            buffer.seek(0)
            return buffer

    # ---------------------- AUDIO ----------------------
    def DownloadAudio(self):
        if not self.yt:
            st.error("❌ No video object available to download audio.")
            return None

        stream = self.yt.streams.filter(only_audio=True, abr=self.quality).first()
        if not stream:
            st.error("❌ No audio stream found.")
            return None

        buffer = io.BytesIO()
        stream.stream_to_buffer(buffer)
        buffer.seek(0)
        return buffer

    # ---------------------- PLAYLIST ----------------------
    def DownloadPlaylist(self):
        if not self.pl:
            try:
                self.pl = Playlist(self.url)
            except Exception as e:
                st.error(f"❌ Failed to parse playlist: {e}")
                return None

        video_urls = list(self.pl.video_urls or [])
        if not video_urls:
            st.error("❌ No videos found in playlist.")
            return None

        import zipfile
        import io

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            for idx, video_url in enumerate(video_urls, 1):
                st.write(f"▶️ Downloading {idx}/{len(video_urls)}: {video_url}")
                try:
                    # ایجاد دانلودر برای هر ویدیو
                    yd = YoutubeDownloader(
                        video_url,
                        Only_audio=self.Only_audio,
                        quality=self.quality
                    )

                    # دریافت buffer ویدیو
                    video_buffer = yd.Download()
                    if video_buffer:
                        # استفاده از عنوان ویدیو برای نام فایل
                        title = yd.yt.title if yd.yt else f"video_{idx}"
                        clean_title = safe_filename(f"{title}_{self.quality}.mp4")
                        zf.writestr(clean_title, video_buffer.getvalue())

                except Exception as e:
                    st.error(f"❌ Error in video {idx}: {e}")

        zip_buffer.seek(0)
        return zip_buffer


    # ---------------------- UTILITIES ----------------------
    def get_available_qualities(self):
        if not self.yt:
            return []
        qualities = set()
        for stream in self.yt.streams.filter(progressive=True, file_extension="mp4"):
            if stream.resolution:
                qualities.add(stream.resolution)
        for stream in self.yt.streams.filter(adaptive=True, mime_type="video/mp4"):
            if stream.resolution:
                qualities.add(stream.resolution)
        return sorted(qualities, key=lambda x: int(x.replace('p', '')), reverse=True)

    def on_progress(self, stream, chunk, bytes_remaining):
        total = getattr(stream, 'filesize', None) or getattr(stream, 'filesize_approx', 0)
        downloaded = total - bytes_remaining
        percent = int(downloaded / total * 100)
        if percent > self.last_percent:
            self.progress_bar.progress(percent)
            self.last_percent = percent

    def on_completed(self, stream, file_path):
        self.progress_bar.progress(100)
        st.success("✅ Download completed!")
