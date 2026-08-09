# 🎬 YouTube Downloader

A modern, fast, and robust YouTube video and audio downloader built with **Streamlit** and **yt-dlp**. Designed to bypass YouTube's aggressive bot-detection (HTTP 403 Forbidden) and provide a clean, user-friendly interface.


## ⚡ Features

- 🎬 **Single Video Tab**: Download any YouTube video in resolutions ranging from **144p** up to **4K (2160p)**.
- 📂 **Playlist Tab**: Load entire playlists and download individual videos/audios manually with a single click.
- 🎵 **Audio Only Tab**: Extract and convert YouTube videos directly into high-quality **MP3** files.
- 📊 **Real-time Download Progress**: Displays active percentage, download speed, total file size, and ETA (estimated time remaining).
- 🔄 **Auto Update**: Quietly checks and updates the core `yt-dlp` package at launch to ensure uninterrupted service against YouTube API changes.
- 🛠️ **Local-First Architecture**: Runs purely on your local network (residential IP), significantly reducing the risk of IP blocks.


## 🚀 Getting Started

### Prerequisites

Make sure you have **Python 3.10+** and **FFmpeg** installed on your system.

> **Note on FFmpeg:** If FFmpeg is not installed globally in your system path, this app will automatically fall back to using the bundled `imageio-ffmpeg` binary, so high-resolution video merging works out of the box!

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/mjmajlesi/YoutubeDownloader.git
   cd YoutubeDownloader
   ```

2. **Install the required packages:**
   ```bash
   pip install -r requirements.txt
   ```

### Running the App

Start the Streamlit server locally:

```bash
streamlit run streamlitMain.py
```

Open your browser and navigate to `http://localhost:8501`.

---

## 📂 Project Structure

```text
YoutubeDownloader/
├── src/
│   ├── main.py          # Core YoutubeDownloader logic (yt-dlp subprocess caller)
│   └── Safe.py          # Filename sanitization and FFmpeg path resolution
├── streamlitMain.py     # Main Streamlit web UI & page routing
├── requirements.txt     # Python dependencies
├── Dockerfile           # Optional containerization config
└── README.md            # You are here!
```

---

## 🔒 Important Note on Download Managers (like IDM)
When downloading files in Streamlit, your download manager (like IDM) may capture the Streamlit temporary media URL instead of the file metadata, saving the file with a hash name like `803958977b9acfd...mp4`.
- **To fix this:** Simply hold the **Alt** key on your keyboard while clicking the **Save** button to let your browser download it natively with the correct title.


## 📝 License

Distributed under the MIT License. See `LICENSE` for more information.
