from pytubefix import YouTube, Playlist
import streamlit as st
import subprocess
import os, re, time, io, shutil, tempfile, uuid, logging
from .safe import safe_filename, safe_youtube, is_playlist_url

class YoutubeDownloader:
    def __init__(self, url):
        self.url = url
        self.st_progress_bar = None
        self.last_percent = 0
        
        # تشخیص نوع URL (playlist یا video)
        self.is_playlist = is_playlist_url(self.url)
        self.yt = None
        self.pl = None
        
        if self.is_playlist:
            try:
                self.pl = Playlist(self.url)
                # Fetch first video to get a 'yt' object for info
                self.yt = safe_youtube(self.pl.video_urls[0])
            except Exception as e:
                st.error(f"❌ Failed to load playlist: {e}")
                self.pl = None
        else:
            try:
                self.yt = safe_youtube(self.url)
            except Exception as e:
                st.error(f"❌ Failed to load video: {e}")
                self.yt = None

    # ---------------------- CALLBACKS ----------------------
    def on_progress(self, stream, chunk, bytes_remaining):
        if not self.st_progress_bar:
            return
            
        total = getattr(stream, 'filesize', None) or getattr(stream, 'filesize_approx', 0)
        if total == 0:
            return
            
        downloaded = total - bytes_remaining
        percent = int(downloaded / total * 100)
        
        # Avoid flooding streamlit with updates
        if percent > self.last_percent:
            self.last_percent = percent
            try:
                self.st_progress_bar.progress(percent, text=f"Downloading... {percent}%")
            except Exception:
                # Handle cases where the progress bar might be gone
                pass

    # ---------------------- VIDEO DOWNLOAD ----------------------
    def Download(self, quality, st_progress_bar=None):
        if not self.yt:
            st.error("❌ No video object available to download.")
            return None
            
        # Register progress bar and reset percent
        self.st_progress_bar = st_progress_bar
        self.last_percent = 0
        self.yt.register_on_progress_callback(self.on_progress)

        if quality == "highest":
            stream = self.yt.streams.get_highest_resolution()
        else:
            stream = self.yt.streams.filter(progressive=True, res=quality, file_extension="mp4").first()

        # Adaptive case (video + audio merge)
        if stream is None:
            st.write("ℹ️ Selected quality is not progressive, attempting to merge audio/video...")
            return self._download_adaptive(quality)
            
        # Progressive case
        else:
            buffer = io.BytesIO()
            stream.stream_to_buffer(buffer)
            buffer.seek(0)
            if self.st_progress_bar:
                self.st_progress_bar.progress(100, text="Download complete! ✅")
            return buffer

    def _download_adaptive(self, quality):
        """Internal helper for FFmpeg merging."""
        video_stream = self.yt.streams.filter(adaptive=True, res=quality, mime_type="video/mp4").first()
        audio_stream = self.yt.streams.filter(adaptive=True, mime_type="audio/mp4").order_by("abr").desc().first()
        
        if not video_stream or not audio_stream:
            st.error(f"❌ No adaptive streams found for {quality}.")
            return None

        if shutil.which("ffmpeg") is None:
            st.error(
                "❌ FFmpeg is not installed. This quality requires merging audio and video. "
                "If running on Streamlit Cloud, add 'ffmpeg' to your packages.txt file."
            )
            return None

        tmpdir = tempfile.gettempdir()
        vid_name = f"temp_video_{uuid.uuid4().hex}.mp4"
        aud_name = f"temp_audio_{uuid.uuid4().hex}.mp4"
        out_name = f"merged_{uuid.uuid4().hex}.mp4"
        
        video_path, audio_path, output_path = None, None, None

        try:
            st.write("Downloading video track...")
            video_path = video_stream.download(output_path=tmpdir, filename=vid_name, max_retries=3)
            st.write("Downloading audio track...")
            audio_path = audio_stream.download(output_path=tmpdir, filename=aud_name, max_retries=3)
            output_path = os.path.join(tmpdir, out_name)

            st.write("Merging files with FFmpeg...")
            cmd = [
                "ffmpeg", "-y",
                "-i", video_path,
                "-i", audio_path,
                "-c", "copy",
                output_path
            ]
            
            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            if proc.returncode != 0:
                logging.error("FFmpeg merge failed: %s", proc.stderr)
                st.error(f"❌ FFmpeg failed: {proc.stderr[:500]}...")
                return None

            with open(output_path, "rb") as f:
                file_data = f.read()
                
            buffer = io.BytesIO(file_data)
            buffer.seek(0)
            if self.st_progress_bar:
                self.st_progress_bar.progress(100, text="Merge complete! ✅")
            return buffer
            
        finally:
            # Cleanup temp files
            for _f in [video_path, audio_path, output_path]:
                try:
                    if _f and os.path.exists(_f):
                        os.remove(_f)
                except Exception as e:
                    logging.warning(f"Failed to remove temp file {_f}: {e}")

    # ---------------------- AUDIO DOWNLOAD ----------------------
    def DownloadAudio(self, quality, st_progress_bar=None):
        if not self.yt:
            st.error("❌ No video object available to download audio.")
            return None

        # Register progress bar and reset percent
        self.st_progress_bar = st_progress_bar
        self.last_percent = 0
        self.yt.register_on_progress_callback(self.on_progress)

        if quality == "highest":
            stream = self.yt.streams.get_audio_only()
        else:
             stream = self.yt.streams.filter(only_audio=True, abr=quality).first()
             
        if not stream:
            st.error(f"❌ No audio stream found for {quality}. Falling back to default.")
            stream = self.yt.streams.get_audio_only()
            if not stream:
                st.error("❌ No audio streams found at all.")
                return None

        buffer = io.BytesIO()
        stream.stream_to_buffer(buffer)
        buffer.seek(0)
        
        if self.st_progress_bar:
            self.st_progress_bar.progress(100, text="Download complete! ✅")
        return buffer

    # ---------------------- PLAYLIST DOWNLOAD ----------------------
    def DownloadPlaylist(self, quality, only_audio=False, st_progress_bar=None):
        if not self.pl:
            st.error("❌ No playlist object available.")
            return None

        video_urls = list(self.pl.video_urls or [])
        if not video_urls:
            st.error("❌ No videos found in playlist.")
            return None

        import zipfile
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            for idx, video_url in enumerate(video_urls, 1):
                progress_text = f"Downloading {idx}/{len(video_urls)}..."
                st.write(f"▶️ {progress_text} {video_url}")
                if st_progress_bar:
                    percent = int(idx / len(video_urls) * 100)
                    st_progress_bar.progress(percent, text=progress_text)
                    
                try:
                    yd_video = YoutubeDownloader(video_url)
                    if not yd_video.yt:
                        st.error(f"❌ Failed to load video {idx}. Skipping.")
                        continue

                    title = yd_video.yt.title
                    
                    if only_audio:
                        video_buffer = yd_video.DownloadAudio(quality=quality, st_progress_bar=None)
                        ext = ".mp3"
                        mime = "audio/mpeg"
                    else:
                        video_buffer = yd_video.Download(quality=quality, st_progress_bar=None)
                        ext = ".mp4"
                        mime = "video/mp4"

                    if video_buffer:
                        clean_title = safe_filename(f"{idx:02d} - {title}{ext}")
                        zf.writestr(clean_title, video_buffer.getvalue())
                        
                except Exception as e:
                    st.error(f"❌ Error on video {idx} ({video_url}): {e}")

        if st_progress_bar:
            st_progress_bar.progress(100, "Playlist Zipped! ✅")
            
        zip_buffer.seek(0)
        return zip_buffer

    # ---------------------- UTILITIES ----------------------
    def get_video_qualities(self):
        if not self.yt:
            return []
        qualities = set()
        for stream in self.yt.streams.filter(file_extension="mp4"):
            if stream.resolution:
                qualities.add(stream.resolution)
        return sorted(qualities, key=lambda x: int(x.replace('p', '')), reverse=True)

    def get_audio_qualities(self):
        if not self.yt:
            return []
        qualities = set()
        for stream in self.yt.streams.filter(only_audio=True, file_extension="mp4"):
             if stream.abr:
                qualities.add(stream.abr)
        # Add a 'highest' option
        qualities = ['highest'] + sorted(list(qualities), key=lambda x: int(x.replace('kbps', '')), reverse=True)
        return list(dict.fromkeys(qualities)) # Remove duplicates

    def get_direct_link(self, quality, only_audio=False):
        """
        NEW: Gets the direct stream URL.
        This is the fix for the IDM problem.
        """
        if not self.yt:
            return None, "Video object not loaded."
            
        try:
            if only_audio:
                if quality == 'highest':
                    stream = self.yt.streams.get_audio_only()
                else:
                    stream = self.yt.streams.filter(only_audio=True, abr=quality).first()
            else:
                if quality == "highest":
                    stream = self.yt.streams.get_highest_resolution()
                else:
                    # Try progressive first
                    stream = self.yt.streams.filter(progressive=True, res=quality, file_extension="mp4").first()
                
                if not stream: # Try adaptive
                    stream = self.yt.streams.filter(adaptive=True, res=quality, mime_type="video/mp4").first()
            
            if stream:
                return stream.url, None
            else:
                return None, f"No stream found for {quality}."
        except Exception as e:
            return None, f"Error getting link: {str(e)}"