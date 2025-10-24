import streamlit as st
from src.main import YoutubeDownloader
st.set_page_config(page_title="YouTube Downloader", page_icon="🎬", layout="centered")
st.title(":zap: YouTube Downloader")
import requests
import base64
import time

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
                buffer = downloader.Download()
                if buffer:
                    st.download_button(
                        label="Save File",
                        data=buffer,
                        file_name="video.mp4",
                        mime="video/mp4"
                    )
                    st.write("")
                    # Offer an optional direct link (uploads file to transfer.sh) so external download managers like IDM can download it.
                    if st.button("🔗 Get direct link (for external download managers)"):
                        with st.spinner("Uploading to get direct link..."):
                            try:
                                # use a sane filename
                                filename = f"video_{int(time.time())}.mp4"
                                # transfer.sh accepts PUT uploads to https://transfer.sh/<filename>
                                url = f"https://transfer.sh/{filename}"
                                # buffer may be a BytesIO or file-like
                                buffer.seek(0)
                                resp = requests.put(url, data=buffer.getvalue(), timeout=120)
                                if resp.status_code in (200, 201):
                                    link = resp.text.strip()
                                    st.success("Direct link created — click to open or copy to clipboard")
                                    st.markdown(f"[Open direct link]({link})")
                                    st.write("Copy this URL and paste it into IDM or your download manager:")
                                    st.code(link)
                                else:
                                    st.error(f"❌ Upload failed (status {resp.status_code}): {resp.text}")
                            except Exception as e:
                                st.error(f"❌ Could not create direct link: {e}")
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
            with st.spinner("Downloading playlist..."):
                downloader = YoutubeDownloader(url, quality=quality)
                zip_buffer = downloader.DownloadPlaylist()
                if zip_buffer:
                    st.download_button(
                        label="💾 Save Playlist ZIP",
                        data=zip_buffer,
                        file_name="playlist_download.zip",
                        mime="application/zip"
                    )
                else:
                    st.error("❌ Failed to download the playlist.")



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




