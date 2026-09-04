# 🎬 YoutubeDownloader

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white" />
  <img src="https://img.shields.io/badge/yt--dlp-FF0000?style=for-the-badge&logo=youtube&logoColor=white" />
  <img src="https://img.shields.io/badge/FFmpeg-007808?style=for-the-badge&logo=ffmpeg&logoColor=white" />
  <br/>
  <img src="https://img.shields.io/github/last-commit/mjmajlesi/YoutubeDownloader?style=flat-square" />
  <img src="https://img.shields.io/badge/license-MIT-green?style=flat-square" />
  <img src="https://img.shields.io/badge/PRs-welcome-brightgreen?style=flat-square" />
</p>

<p align="center"><b>English</b> | <a href="#-فارسی">فارسی</a></p>

> A fast, reliable YouTube downloader that actually works on Streamlit Cloud. Built on `yt-dlp` + `FFmpeg` with automatic SABR / 403 fallback, live progress, and playlist support.

---

## ✨ Features

| Feature | Details |
|---|---|
| 🎥 Single video | Any public video, 144p → 2160p (4K) |
| 📃 Playlist | Flat-loads the whole list, shows thumbs; downloads any entry individually |
| 🎵 Audio only | Video → MP3 (192 kbps) via FFmpeg extract |
| 📊 Live progress | `%` · size · speed · ETA + *Merging / Extracting* phases |
| 🛡️ SABR / 403 resilient | Retries `web → tv → mweb → android → ios` on 403 / `needs to be reloaded` |
| 🟢 Cloud-ready | `packages.txt` installs `ffmpeg` + `nodejs` so JS deciphering works on Streamlit Cloud |
| ⚡ Auto-update | Quiet `pip install -U yt-dlp` on first load (like `reclip`) |

## 🚀 Quick start (local)

```bash
git clone https://github.com/mjmajlesi/YoutubeDownloader.git
cd YoutubeDownloader
pip install -r requirements.txt
streamlit run streamlitMain.py
# → http://localhost:8501
```

> **FFmpeg note:** if `ffmpeg` is not on your `PATH`, the app falls back to the bundled `imageio-ffmpeg` binary. On Streamlit Cloud it comes from `packages.txt`.

> **JS runtime note:** current YouTube SABR requires a JS runtime. Install one locally for best results:
> `winget install DenoLand.Deno` or `winget install OpenJS.NodeJS` (Windows) /
> `brew install deno` (macOS) / `sudo apt install nodejs` (Linux). The app auto-detects `deno`/`node` and passes `--js-runtimes`.

## 🗂️ Project structure

```
YoutubeDownloader/
├── streamlitMain.py        # Streamlit UI — 3 tabs (Single / Playlist / Audio)
├── src/
│   ├── main.py             # YoutubeDownloader — yt-dlp subprocess + fallback + progress
│   └── Safe.py             # safe_filename + FFmpeg path helper
├── streamlit/config.toml   # dark theme
├── packages.txt            # apt packages for Streamlit Cloud (ffmpeg + nodejs)
├── requirements.txt
└── README.md
```

## 🔧 How it works

* **Metadata** — `yt-dlp -J --flat-playlist` for playlists (fast), full `-J` for single videos. On 403/SABR (`The page needs to be reloaded`) it retries with `player_client=tv/mweb/android`.
* **Download** — `yt-dlp --newline -o %(id)s.%(ext)s --merge-output-format mp4` streamed via `Popen`; progress is parsed with a regex and pushed to `st.progress`. On SABR it retries across 5 clients and relaxes the format on `android`/`ios`.
* **JS deciphering** — if `deno` or `node` is found (`shutil.which`), `--js-runtimes` is injected into every `yt-dlp` call — required since YouTube's 2025 SABR change, and essential on Streamlit Cloud (provided by `nodejs` in `packages.txt`).

## ❓ Troubleshooting

| Symptom | Fix |
|---|---|
| `HTTP Error 403: Forbidden` / `The page needs to be reloaded` | `pip install -U yt-dlp` + install `deno`/`node`. On Streamlit Cloud, after pushing `packages.txt` do *Reboot app* in the dashboard. |
| `No supported JavaScript runtime` warning | Install `deno` or `nodejs` (see above). |
| `Could not locate downloaded file. Files in temp: []` | Was a swallowed block error — now surfaced with a clear hint. Update `yt-dlp` + runtime as above. |
| `ffmpeg not found` at high res | Install `ffmpeg` globally or keep `imageio-ffmpeg` in `requirements.txt` (already there). |

## 📄 License

MIT — see [LICENSE](LICENSE).

---

## 🇮🇷 فارسی

یک دانلودر سریع و مطمئن یوتیوب که روی **Streamlit Cloud** هم کار می‌کند. با `yt-dlp` و `FFmpeg` ساخته شده، با فال‌بک خودکار برای خطاهای SABR / 403، نمایش زندهٔ درصد و سرعت، و پشتیبانی از پلی‌لیست.

### قابلیت‌ها

- تک‌ویدیو از 144p تا 2160p، پلی‌لیست کامل، استخراج MP3
- نوار پیشرفت زنده (درصد · حجم · سرعت · ETA)
- مقاوم در برابر 403/SABR با تلاش روی کلاینت‌های `web → tv → mweb → android → ios`
- آمادهٔ کلاد: `packages.txt` هم `ffmpeg` و هم `nodejs` را روی Streamlit Cloud نصب می‌کند

### اجرای لوکال

```bash
git clone https://github.com/mjmajlesi/YoutubeDownloader.git
cd YoutubeDownloader
pip install -r requirements.txt
streamlit run streamlitMain.py
```

برای پایداری بیشتر یک JS runtime نصب کنید: `winget install DenoLand.Deno` یا `winget install OpenJS.NodeJS`.
