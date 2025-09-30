"""
  Author : MohammadJavadMajlesi
"""

from pytubefix import YouTube
from pathlib import Path
from tqdm import tqdm


class YoutubeDownloader:
  def __init__(self , url , Only_audio=False , path_output=None , quality=None ):
    self.url = url
    self.Only_audio = Only_audio
    self.path_output = path_output or Path().cwd()
    self.quality = quality or "highest"
    self.pbar = None

  def Download(self):
    yt = YouTube(
      self.url ,
      on_progress_callback=self.on_progress,
      on_complete_callback=self.on_completed
    )
    if self.Only_audio:
       stream = yt.streams.filter(only_audio=True).first()
    else:
      if self.quality == "highest":
        stream = yt.streams.filter(progressive=True, file_extension='mp4').get_highest_resolution()
      else:
        stream = yt.streams.filter(res=self.quality, progressive=True , file_extension='mp4').first()

    if stream is None:
      print(f"No stream found with quality {self.quality}. Available qualities:")
      available_qualities = [s.resolution for s in yt.streams.filter(progressive=True, file_extension='mp4')]
      print(", ".join(available_qualities))
      return

    self.pbar = tqdm(
      total= stream.filesize ,
      desc="Downloading... " ,
      unit="B",
      unit_scale=True,
      colour="green",
    )
    stream.download(output_path=self.path_output)

  def on_progress(self, stream, chunk, bytes_remaining):
    current = stream.filesize - bytes_remaining
    self.pbar.update(current - self.pbar.n)


  def on_completed(self, steam , file_path):
    print()
    print(f"Download completed! File saved to: {file_path}")

if __name__ == "__main__":
  url = input("Enter the YouTube video URL: ")
  only_audio = input("Download only audio? (yes/no): ").strip().lower() == 'yes'
  path_output = input("Enter the output path (leave blank for current directory): ").strip() or None
  quality = input("Enter the desired quality (e.g., '720p', '1080p', or 'highest'): ").strip() or None

  downloader = YoutubeDownloader(url, Only_audio=only_audio, path_output=path_output, quality=quality)
  downloader.Download()
