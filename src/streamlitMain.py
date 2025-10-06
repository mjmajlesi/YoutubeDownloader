import streamlit as st
from src.main import YoutubeDownloader

st.set_page_config(page_title="YouTube Downloader", page_icon="🎬", layout="centered")
st.title(":zap: YouTube Downloader")

# انتخاب نوع دانلود
download_mode = st.radio(
    "Select Download Type:",
    ["Video", "Playlist", "Audio"],
    horizontal=True,
)

# ------------------------------------------
# 🎬 VIDEO MODE
# ------------------------------------------
if download_mode == "Video":
    url = st.text_input("Enter YouTube Video URL")

    if url:
        # ساخت دانلودر برای گرفتن کیفیت‌ها
        try:
            downloader = YoutubeDownloader(url)
            selected_quality = downloader.get_available_qualities()
            quality = st.selectbox("Select Quality", selected_quality)
            downloader.quality = quality
        except Exception as e:
            st.error(f"⚠️ Could not load video info: {e}")
            quality = None
    else:
        quality = None

    # فقط وقتی کیفیت انتخاب شده دکمه نشون داده میشه
    if quality:
        st.write("")  # فاصله کوچک برای زیبایی
        if st.button("⬇️ Download Video"):
            with st.spinner("Downloading..."):
                downloader = YoutubeDownloader(url, quality=quality)
                file_path = downloader.Download()
                if file_path:
                    with open(file_path, "rb") as file:
                        st.download_button(
                            label="Save File",
                            data=file,
                            file_name=file_path.split("/")[-1],
                            mime="video/mp4",
                            key="video_download_btn",
                        )
                else:
                    st.error("❌ Failed to download the video.")
    elif url:
        st.info("ℹ️ Please select a quality first.")


# ------------------------------------------
# 📂 PLAYLIST MODE
# ------------------------------------------
elif download_mode == "Playlist":
    url = st.text_input("Enter YouTube Playlist URL")
    quality = st.selectbox("Select Quality", ('highest', '1080p', '720p', '480p', '360p'), key="playlist_quality")

    if url and quality:
        if st.button("⬇️ Download Playlist"):
            downloader = YoutubeDownloader(url, quality=quality)
            files = downloader.DownloadPlaylist()
            if files:
                st.success(f"✅ Downloaded {len(files)} videos successfully!")
            else:
                st.error("❌ Failed to download the playlist.")
    elif url:
        st.info("ℹ️ Please select a quality first.")


# ------------------------------------------
# 🎵 AUDIO MODE
# ------------------------------------------
elif download_mode == "Audio":
    url = st.text_input("Enter YouTube Audio URL")
    quality = st.selectbox("Select Audio Quality", ('highest', '128kbps', '64kbps'), key="audio_quality")

    if url and quality:
        if st.button("⬇️ Download Audio"):
            downloader = YoutubeDownloader(url, Only_audio=True, quality=quality)
            file_path = downloader.Download()
            if file_path:
                with open(file_path, "rb") as file:
                    st.download_button(
                        label="Save Audio",
                        data=file,
                        file_name=file_path.split("/")[-1],
                        mime="audio/mp3",
                        key="audio_download_btn",
                    )
            else:
                st.error("❌ Failed to download audio.")
    elif url:
        st.info("ℹ️ Please select audio quality first.")




