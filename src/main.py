"""
  Author : MohammadJavadMajlesi
"""

from pytube import YouTube
from pathlib import Path


class YoutubeDownloader:
  def __init__(self , url , Only_audio=False , path_output=None , quality=None ):
    self.url = url
    self.Only_audio = Only_audio
    self.path_output = path_output or Path().cwd()
    self.quality = quality or "highest"

  def Download(self):
    yt = YouTube(self.url)
    if self.Only_audio:
      stream = yt.streams.filter(res=self.quality, only_audio=True).first()
    else:
      if self.quality == "highest":
        stream = yt.streams.filter(progressive= True , file_extension='mp4').get_highest_resolution()
      else:
        stream = yt.streams.filter(res=self.quality, progressive=True , file_extension='mp4').first()

    stream.download(output_path=self.path_output)
    print("Download Completed!")
