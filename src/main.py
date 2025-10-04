from pytubefix import YouTube , Playlist
from pathlib import Path
import streamlit as st
import subprocess
import os, re, time
from urllib.error import URLError
from src.Safe import safe_filename, safe_youtube, is_playlist_url

class YoutubeDownloader:
    def __init__(self, url, Only_audio=False, path_output=None, quality=None):
        self.url = url
        self.Only_audio = Only_audio
        self.path_output = path_output or Path().cwd()
        self.quality = quality or "highest"
        self.progress_bar = st.progress(0)
        self.last_percent = 0

        # Don't try to create a YouTube object for playlist URLs
        self.is_playlist = is_playlist_url(self.url)
        self.yt = None
        self.pl = None
        if self.is_playlist:
            try:
                self.pl = Playlist(self.url)
            except Exception:
                # Leave pl as None; methods will handle None appropriately
                self.pl = None
        else:
            # Video URL
            self.yt = safe_youtube(self.url)
            # وصل کردن callbacks بعد از ساخت
            self.yt.register_on_progress_callback(self.on_progress)
            self.yt.register_on_complete_callback(self.on_completed)

    def Download(self):
        if not self.yt:
            st.error("❌ No video object available to download.")
            return None

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

    def DownloadAudio(self):
        if self.is_playlist:
            st.error("❌ The provided URL is a playlist. Use DownloadPlaylist() for playlists.")
            return None

        if not self.yt:
            st.error("❌ No video object available to download audio.")
            return None

        if self.Only_audio:
            stream = self.yt.streams.filter(only_audio=True , abr=self.quality).first()
            if not stream:
                st.error("❌ No audio stream found.")
                return None
            return stream.download(output_path=self.path_output , filename=safe_filename(f"{self.yt.title}_{self.quality}.mp3"))


    def DownloadPlaylist(self):
        # If pl is not initialized or URL is not a playlist, try to create a Playlist
        if not self.pl:
            try:
                self.pl = Playlist(self.url)
            except Exception as e:
                st.error(f"❌ Failed to parse playlist: {e}")
                return None

        output_files = []
        video_urls = list(self.pl.video_urls or [])
        if not video_urls:
            st.error("❌ No videos found in playlist.")
            return None

        for idx, video_url in enumerate(video_urls, 1):
            st.write(f"▶️ Downloading {idx}/{len(video_urls)}: {video_url}")
            try:
                # For each video, create a downloader for the video URL (not the playlist)
                yd = YoutubeDownloader(
                    video_url,
                    Only_audio=self.Only_audio,
                    path_output=self.path_output,
                    quality=self.quality
                )
                file_path = yd.Download()
                if file_path:
                    output_files.append(file_path)
            except Exception as e:
                st.error(f"❌ Error in video {idx}: {e}")

        # If we downloaded one or more files, create a zip archive and return its path
        if output_files:
            import zipfile

            zip_name = safe_filename(f"playlist_{int(time.time())}.zip")
            zip_path = os.path.join(self.path_output, zip_name)
            try:
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                    for f in output_files:
                        # add file with only the filename, not full path
                        try:
                            zf.write(f, arcname=os.path.basename(f))
                        except Exception:
                            # skip any file that can't be added
                            pass
                return zip_path
            except Exception as e:
                st.error(f"❌ Failed to create zip archive: {e}")
                return None
        return None

    # def DownloadCaptions(self):
    #     if self.is_playlist:
    #         st.error("❌ Captions for playlists are not supported.")
    #         return None

    #     if not self.yt:
    #         st.error("❌ No video object available to fetch captions.")
    #         return None

    #     captions = self.yt.captions
    #     if not captions:
    #         st.error("❌ No captions available for this video.")
    #         return None
    #     # Persian Language
    #     if captions.get_by_language_code('fa') or captions.get_by_language_code('a.fa'):
    #         caption = captions.get_by_language_code('fa') or captions.get_by_language_code('a.fa')
    #     # English Language
    #     else:
    #         caption = captions.get_by_language_code('en') or captions.get_by_language_code('a.en')
    #     if not caption:
    #         st.error("❌ No English captions available.")
    #         return None
    #     caption_text = caption.generate_srt_captions()
    #     filename = safe_filename(f"{self.yt.title}_captions.srt")
    #     file_path = os.path.join(self.path_output, filename)
    #     with open(file_path, "w", encoding="utf-8") as f:
    #         f.write(caption_text)
    #     return file_path


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
