"""
    YoutubeDownloader - A clean, robust downloader using yt-dlp CLI via subprocess.
    Bypasses YouTube bot-protection (403 errors) using player client rotation.
    Author: Mohammad Javad Majlesi
"""

import io
import os
import re
import time
import glob
import shutil
import tempfile
import logging
import subprocess
import json

try:
    import streamlit as st
except ImportError:
    st = None

from src.Safe import safe_filename, get_ffmpeg_path, has_ffmpeg


class VideoInfo:
    """Represents metadata for a single YouTube video."""
    def __init__(self, info_dict):
        self._info = info_dict or {}
        self.title = self._info.get("title", "Unknown Title")
        self.video_id = self._info.get("id") or self._info.get("video_id")
        self.thumbnail_url = self._info.get("thumbnail") or ""
        self.author = self._info.get("uploader") or self._info.get("channel") or "Unknown"
        self.views = self._info.get("view_count") or 0
        self.length = self._info.get("duration") or 0
        self.watch_url = self._info.get("webpage_url") or f"https://www.youtube.com/watch?v={self.video_id}" if self.video_id else ""

    def __str__(self):
        return self.title


class PlaylistInfo:
    """Represents a YouTube playlist."""
    def __init__(self, title, videos):
        self.title = title or "Playlist"
        self.videos = videos or []
        self.author = "YouTube"

    def __len__(self):
        return len(self.videos)


class YoutubeDownloader:
    def __init__(self, url: str):
        self.url = url
        self.st_progress_bar = None
        self.is_playlist = self._check_playlist_url(self.url)
        self.yt = None
        self.pl = None
        self.info = None
        self.error = None

        if not self.url:
            self.error = "Please provide a valid YouTube URL."
            return

        try:
            if self.is_playlist:
                self._load_playlist()
            else:
                self._load_video()
        except Exception as e:
            self.error = str(e)
            if st is not None:
                st.error(f"❌ Failed to load: {self.error}")

    @staticmethod
    def _check_playlist_url(url: str) -> bool:
        return 'list=' in url or '/playlist' in url

    def _extract_ytdlp_info(self, url, flat=True):
        """Fetches metadata using yt-dlp JSON extraction."""
        cmd = [
            "yt-dlp",
            "--quiet",
            "--no-warnings",
            "-J",
        ]
        if flat:
            cmd.append("--flat-playlist")
        cmd.append(url)

        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        if proc.returncode != 0:
            # Retry without flat flag if extraction failed
            if flat:
                return self._extract_ytdlp_info(url, flat=False)
            raise RuntimeError(proc.stderr.strip() or f"yt-dlp exited with code {proc.returncode}")

        try:
            return json.loads(proc.stdout)
        except Exception as e:
            raise RuntimeError(f"Failed to parse yt-dlp output: {e}")

    def _load_video(self):
        info = self._extract_ytdlp_info(self.url, flat=False)
        self.info = info
        self.yt = VideoInfo(info)

    def _load_playlist(self):
        info = self._extract_ytdlp_info(self.url, flat=True)
        title = info.get("title", "Untitled Playlist")

        entries = info.get("entries", [])
        videos = []
        for entry in entries:
            if not entry:
                continue
            video_id = entry.get("id") or entry.get("video_id")
            if not video_id:
                m = re.search(r"[?&]v=([^&]+)", str(entry.get("url", "")))
                video_id = m.group(1) if m else None
            if not video_id:
                continue

            # Extract thumbnail url from flat entries
            thumb_url = ""
            thumbnails = entry.get("thumbnails", [])
            if thumbnails:
                thumb_url = thumbnails[-1].get("url", "")
            if not thumb_url and video_id:
                thumb_url = f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"

            videos.append(VideoInfo({
                "title": entry.get("title", "Untitled"),
                "id": video_id,
                "thumbnail": thumb_url,
                "uploader": entry.get("uploader", entry.get("channel", "")),
                "view_count": entry.get("view_count", 0),
                "duration": entry.get("duration", 0),
                "webpage_url": f"https://www.youtube.com/watch?v={video_id}",
            }))

        self.pl = PlaylistInfo(title, videos)
        if videos:
            self.yt = videos[0]
            # Fetch first video's full formats to use as a proxy for qualities
            try:
                self.info = self._extract_ytdlp_info(self.yt.watch_url, flat=False)
            except Exception:
                pass

    def get_video_qualities(self):
        """Returns available video resolutions (e.g. ['1080p', '720p', ...])."""
        if not self.info:
            return ["highest"]

        heights = set()
        for fmt in self.info.get("formats", []):
            if fmt.get("vcodec", "none") != "none" and fmt.get("height"):
                heights.add(int(fmt["height"]))

        if heights:
            return sorted(
                (f"{h}p" for h in heights if h > 0),
                key=lambda x: int(x.replace("p", "")),
                reverse=True
            )
        return ["highest"]

    def get_audio_qualities(self):
        """Returns available audio bitrates (e.g. ['highest', '128kbps', ...])."""
        if not self.info:
            return ["highest"]

        abrs = set()
        for fmt in self.info.get("formats", []):
            if fmt.get("acodec", "none") != "none" and fmt.get("abr"):
                abrs.add(int(fmt["abr"]))

        if abrs:
            return ["highest"] + [
                f"{v}kbps" for v in sorted(abrs, reverse=True)
            ]
        return ["highest"]

    def Download(self, quality, st_progress_bar=None, only_audio=False):
        """Downloads the video/audio to a BytesIO buffer with real-time progress."""
        self.st_progress_bar = st_progress_bar
        out_dir = tempfile.mkdtemp(prefix="ytdlp_")

        try:
            fmt = self._select_ytdlp_format(quality, only_audio)
            ff = get_ffmpeg_path()

            cmd = [
                "yt-dlp",
                "--no-playlist",
                "--restrict-filenames",
                "--newline",  # Ensures progress is printed on newlines
                "--format", fmt,
                "-o", os.path.join(out_dir, "%(id)s.%(ext)s"),
                "--merge-output-format", "mp4",
                "--add-header", "User-Agent:Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            ]

            if only_audio:
                if ff:
                    cmd += [
                        "-x",
                        "--audio-format", "mp3",
                        "--audio-quality", "192",
                        "--ffmpeg-location", os.path.dirname(ff),
                    ]
            else:
                if ff:
                    cmd += ["--ffmpeg-location", os.path.dirname(ff)]

            cmd.append(self.url)

            # Spawn process to stream output
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1
            )

            progress_pattern = re.compile(
                r"\[download\]\s+(\d+(?:\.\d+)?)%\s+of\s+(~?\s*[\d\.]+\w+)\s+at\s+([\d\.]+\w+/s|\w+/s)\s+ETA\s+([\d:]+)"
            )

            stderr_lines = []
            for line in proc.stdout:
                line_str = line.strip()
                m = progress_pattern.search(line_str)
                if m:
                    pct, size, speed, eta = m.groups()
                    if self.st_progress_bar:
                        try:
                            # Clamp percentage between 0 and 98 to keep 100 for final merge/file writing status
                            val = min(98, int(float(pct)))
                            self.st_progress_bar.progress(
                                val,
                                text=f"Downloading: {pct}% | Size: {size} | Speed: {speed} | ETA: {eta}"
                            )
                        except Exception:
                            pass
                elif "[Merger]" in line_str or "Merging formats" in line_str:
                    if self.st_progress_bar:
                        try:
                            self.st_progress_bar.progress(99, text="Merging video and audio tracks...")
                        except Exception:
                            pass
                elif "[ExtractAudio]" in line_str or "Extracting audio" in line_str:
                    if self.st_progress_bar:
                        try:
                            self.st_progress_bar.progress(99, text="Extracting and converting audio to MP3...")
                        except Exception:
                            pass

                if "ERROR:" in line_str or "unavailable" in line_str.lower():
                    stderr_lines.append(line_str)

            proc.wait()

            if proc.returncode != 0:
                err_msg = "\n".join(stderr_lines) if stderr_lines else f"yt-dlp exited with code {proc.returncode}"
                raise RuntimeError(err_msg)

            # Locate the produced file
            produced = self._find_produced_file(out_dir)
            if not produced:
                files_found = os.listdir(out_dir) if os.path.exists(out_dir) else []
                raise RuntimeError(f"Could not locate downloaded file. Files in temp: {files_found}")

            with open(produced, "rb") as f:
                data = f.read()

            buffer = io.BytesIO(data)
            buffer.seek(0)

            if self.st_progress_bar:
                try:
                    self.st_progress_bar.progress(100, text="Download complete! ✅")
                except Exception:
                    pass

            return buffer

        except Exception as e:
            if st is not None:
                st.error(f"❌ yt-dlp download failed: {e}")
            return None
        finally:
            shutil.rmtree(out_dir, ignore_errors=True)

    def DownloadAudio(self, quality, st_progress_bar=None):
        return self.Download(quality, st_progress_bar=st_progress_bar, only_audio=True)

    def _select_ytdlp_format(self, quality, only_audio):
        if only_audio:
            if quality in ("highest", "best"):
                return "bestaudio/best"
            kbps = int(quality.replace("kbps", "").replace("Kbps", ""))
            return f"bestaudio[abr<={kbps}]/bestaudio/best"

        if quality in ("highest", "best"):
            return "bestvideo+bestaudio/best"

        h = quality.replace("p", "").replace("P", "")
        if h.isdigit():
            h = int(h)
            return f"bestvideo[height<={h}]+bestaudio/best[height<={h}]/best"
        return "bestvideo+bestaudio/best"

    def _find_produced_file(self, out_dir):
        files = []
        for root, dirs, fnames in os.walk(out_dir):
            for f in fnames:
                if not f.endswith(('.part', '.ytdl')):
                    files.append(os.path.join(root, f))
        if not files:
            return None
        return max(files, key=os.path.getsize)
