from pytubefix import YouTube
from pathlib import Path
import streamlit as st

class YoutubeDownloader:
    def __init__(self, url, Only_audio=False, path_output=None, quality=None):
        self.url = url
        self.Only_audio = Only_audio
        self.path_output = path_output or Path().cwd()
        self.quality = quality or "highest"
        self.st_progress = st.progress(0)
        self.last_percent = 0

    def Download(self):
        yt = YouTube(
            self.url,
            on_progress_callback=self.on_progress,
            on_complete_callback=self.on_completed
        )

        if self.Only_audio:
            stream = yt.streams.filter(only_audio=True).first()
        else:
            if self.quality == "highest":
                stream = yt.streams.filter(progressive=True, file_extension='mp4').get_highest_resolution()
            else:
                stream = yt.streams.filter(res=self.quality, progressive=True, file_extension='mp4').first()
                if stream is None:
                    stream = yt.streams.filter(res=self.quality, progressive=True , file_extension='mp4').first()

        if stream is None:
            st.error(f"No stream found with quality {self.quality}")
            return None

        file_path = stream.download(output_path=self.path_output)
        return file_path

    def on_progress(self, stream, chunk, bytes_remaining):
        total_size = stream.filesize
        bytes_downloaded = total_size - bytes_remaining
        percent = int(bytes_downloaded / total_size * 100)
        if percent > self.last_percent:
            self.st_progress.progress(percent / 100.0)
            self.last_percent = percent

    def on_completed(self, stream, file_path):
        self.st_progress.progress(1.0)
        st.success("Download completed!")
