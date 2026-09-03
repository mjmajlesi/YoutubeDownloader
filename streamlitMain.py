import os
import time
import tempfile
import streamlit as st

# --- Startup yt-dlp Auto-Update (similar to reclip) + Deno check ---
import subprocess
import shutil

if 'ytdlp_updated' not in st.session_state:
    try:
        # yt-dlp now requires a JS runtime (deno/node) for signature deciphering
        if shutil.which("deno") is None and shutil.which("node") is None:
            try:
                st.toast("⚠️ yt-dlp recommends deno/node for reliable downloads. Some videos may show 'needs to be reloaded' without it.", icon="⚠️")
            except Exception:
                pass
        subprocess.run(["pip", "install", "-q", "-U", "yt-dlp"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        st.session_state.ytdlp_updated = True
    except Exception:
        pass

from src.main import YoutubeDownloader
from src.Safe import safe_filename

# --- Page Config ---
st.set_page_config(page_title="YouTube Downloader", page_icon="🎬", layout="centered")
st.title("🚀 YouTube Downloader")

# --- Initialize Session State ---
if 'downloader' not in st.session_state:
    st.session_state.downloader = None
if 'video_buffer' not in st.session_state:
    st.session_state.video_buffer = None
if 'audio_buffer' not in st.session_state:
    st.session_state.audio_buffer = None
if 'playlist_buffers' not in st.session_state:
    st.session_state.playlist_buffers = {}
if 'current_url' not in st.session_state:
    st.session_state.current_url = ""

# --- Helper function to reset state on new URL ---
def reset_state_on_new_url(new_url):
    if new_url != st.session_state.current_url:
        st.session_state.downloader = None
        st.session_state.video_buffer = None
        st.session_state.audio_buffer = None
        st.session_state.playlist_buffers = {}
        st.session_state.current_url = new_url

# --- UI Tabs ---
tab1, tab2, tab3 = st.tabs(["🎬 Single Video", "📂 Playlist", "🎵 Audio Only"])

# ------------------------------------------
# 🎬 SINGLE VIDEO TAB
# ------------------------------------------
with tab1:
    st.header("Single Video Download")
    url = st.text_input("Enter YouTube Video URL", key="video_url_input")

    reset_state_on_new_url(url)

    if url:
        # Load downloader object into session state if it's not there or URL changed
        if not st.session_state.downloader:
            with st.spinner("Loading video info..."):
                try:
                    st.session_state.downloader = YoutubeDownloader(url=url)
                except Exception as e:
                    st.error(f"❌ Failed to load video. Check URL or try again. Error: {e}")
                    st.session_state.downloader = None

        # --- Display Video Info and Download Options ---
        if st.session_state.downloader and st.session_state.downloader.yt:
            yt = st.session_state.downloader.yt

            col1, col2 = st.columns([1, 2])
            with col1:
                if yt.thumbnail_url:
                    st.image(yt.thumbnail_url, width='stretch')
                else:
                    st.info("No thumbnail available")
            with col2:
                st.subheader(yt.title)
                length_str = time.strftime('%H:%M:%S', time.gmtime(yt.length)) if yt.length else "Unknown"
                st.caption(f"by {yt.author} | {yt.views:,} views | Length: {length_str}")

            st.divider()

            # --- Quality Selection ---
            video_qualities = st.session_state.downloader.get_video_qualities()
            if not video_qualities:
                st.warning("No standard video streams found. Trying fallback options...")
                video_qualities = ["highest"]

            quality = st.selectbox("Select Video Quality", video_qualities, key="video_quality_select")

            # --- Download Buttons ---
            if st.button("⬇️ Download Video", key="video_download_button"):
                st.session_state.video_buffer = None # Clear old buffer
                progress_bar = st.progress(0, text="Starting download...")
                with st.spinner("Downloading..."):
                    try:
                        buffer = st.session_state.downloader.Download(
                            quality=quality,
                            st_progress_bar=progress_bar
                        )
                        st.session_state.video_buffer = buffer
                    except Exception as e:
                        st.error(f"❌ Download failed: {e}")
                        progress_bar.empty()

            # --- Show Save Button if buffer is ready ---
            if st.session_state.video_buffer:
                file_name = safe_filename(f"{yt.title}_{quality}.mp4")
                st.download_button(
                    label="💾 Save Video File",
                    data=st.session_state.video_buffer,
                    file_name=file_name,
                    mime="video/mp4"
                )

# ------------------------------------------
# 📂 PLAYLIST TAB
# ------------------------------------------
with tab2:
    st.header("Playlist Download")
    pl_url = st.text_input("Enter YouTube Playlist URL", key="playlist_url_input")

    reset_state_on_new_url(pl_url)

    if pl_url:
        if not st.session_state.downloader:
            with st.spinner("Loading playlist info... This may take a moment."):
                try:
                    st.session_state.downloader = YoutubeDownloader(url=pl_url)
                except Exception as e:
                    st.error(f"❌ Failed to load playlist. Check URL or try again. Error: {e}")
                    st.session_state.downloader = None

        # --- Display Playlist Info and Download Options ---
        if st.session_state.downloader and st.session_state.downloader.pl:
            pl = st.session_state.downloader.pl
            yt_info = st.session_state.downloader.yt # Get info from first video

            st.subheader(pl.title)
            st.caption(f"Playlist by {pl.author} | {len(pl.videos)} videos found")
            st.divider()

            col1, col2 = st.columns(2)
            with col1:
                download_type = st.radio("Download as:", ("Video", "Audio"), horizontal=True, key="playlist_type_radio")

            with col2:
                # --- Conditional Quality Selectors ---
                if download_type == "Video":
                    # Use first video's qualities or default resolutions
                    video_qualities = st.session_state.downloader.get_video_qualities()
                    if not video_qualities:
                        video_qualities = ["highest", "1080p", "720p", "480p", "360p"]
                    quality = st.selectbox("Select Video Quality", video_qualities, key="playlist_quality_select_vid")
                else:
                    audio_qualities = st.session_state.downloader.get_audio_qualities()
                    quality = st.selectbox("Select Audio Quality", audio_qualities, key="playlist_quality_select_aud")

            st.divider()
            st.write(f"**Found {len(pl.videos)} videos:**")

            # --- Iterate through all videos and create an expander for each ---
            for idx, yt in enumerate(pl.videos, 1):
                video_id = yt.video_id or f"vid_{idx}"

                # Check for empty titles
                title_text = yt.title or f"Video {idx}"
                length_text = time.strftime('%M:%S', time.gmtime(yt.length)) if yt.length else "Unknown"

                with st.expander(f"**{idx}. {title_text}** ({length_text})"):

                    c1, c2 = st.columns([1, 2])
                    with c1:
                        if yt.thumbnail_url:
                            st.image(yt.thumbnail_url, width='stretch')
                        else:
                            st.info("No thumbnail")
                    with c2:
                        st.caption(f"by {yt.author} | {yt.views:,} views")

                        # --- Button: Manual Download ---
                        file_ext = ".mp3" if download_type == "Audio" else ".mp4"
                        mime_type = "audio/mpeg" if download_type == "Audio" else "video/mp4"
                        file_name = safe_filename(f"{title_text}{file_ext}")

                        if st.button("⬇️ Manual Download", key=f"dl_btn_{video_id}"):
                            # Clear buffer for this specific video
                            st.session_state.playlist_buffers[video_id] = None

                            progress_placeholder = st.empty() # Placeholder for this video's progress bar
                            progress_bar = progress_placeholder.progress(0, text="Starting download...")

                            with st.spinner(f"Downloading: {title_text}..."):
                                try:
                                    # Create downloader just-in-time
                                    video_downloader = YoutubeDownloader(url=yt.watch_url)

                                    if download_type == "Audio":
                                        buffer = video_downloader.DownloadAudio(
                                            quality=quality,
                                            st_progress_bar=progress_bar
                                        )
                                    else:
                                        buffer = video_downloader.Download(
                                            quality=quality,
                                            st_progress_bar=progress_bar
                                        )

                                    if buffer:
                                        # Save buffer to our dictionary with video_id as key
                                        st.session_state.playlist_buffers[video_id] = buffer
                                        progress_placeholder.empty() # Clear progress bar
                                    else:
                                        st.error("Download failed, buffer is empty.")
                                        progress_placeholder.empty()

                                except Exception as e:
                                    st.error(f"❌ Download failed: {e}")
                                    progress_placeholder.empty()

                        # --- Show the actual download button if the buffer exists ---
                        if st.session_state.playlist_buffers.get(video_id):
                            st.download_button(
                                label=f"💾 Save {file_name}",
                                data=st.session_state.playlist_buffers[video_id],
                                file_name=file_name,
                                mime=mime_type,
                                key=f"save_btn_{video_id}"
                            )

# ------------------------------------------
# 🎵 AUDIO ONLY TAB
# ------------------------------------------
with tab3:
    st.header("Audio Only Download")
    audio_url = st.text_input("Enter YouTube Video URL", key="audio_url_input")

    reset_state_on_new_url(audio_url)

    if audio_url:
        if not st.session_state.downloader:
            with st.spinner("Loading audio info..."):
                try:
                    st.session_state.downloader = YoutubeDownloader(url=audio_url)
                except Exception as e:
                    st.error(f"❌ Failed to load video. Check URL or try again. Error: {e}")
                    st.session_state.downloader = None

        # --- Display Video Info and Download Options ---
        if st.session_state.downloader and st.session_state.downloader.yt:
            yt = st.session_state.downloader.yt

            col1, col2 = st.columns([1, 2])
            with col1:
                if yt.thumbnail_url:
                    st.image(yt.thumbnail_url, width='stretch')
                else:
                    st.info("No thumbnail available")
            with col2:
                st.subheader(yt.title)
                st.caption(f"by {yt.author} | {yt.views:,} views")

            st.divider()

            # --- Quality Selection ---
            audio_qualities = st.session_state.downloader.get_audio_qualities()
            if not audio_qualities:
                st.warning("No audio streams found.")
            else:
                audio_quality = st.selectbox("Select Audio Quality", audio_qualities, key="audio_quality_select")

                # --- Download Buttons ---
                if st.button("⬇️ Download Audio", key="audio_download_button"):
                    st.session_state.audio_buffer = None # Clear old buffer
                    progress_bar = st.progress(0, text="Starting download...")
                    with st.spinner("Downloading..."):
                        try:
                            buffer = st.session_state.downloader.DownloadAudio(
                                quality=audio_quality,
                                st_progress_bar=progress_bar
                            )
                            st.session_state.audio_buffer = buffer
                        except Exception as e:
                            st.error(f"❌ Download failed: {e}")
                            progress_bar.empty()

                # --- Show Save Button if buffer is ready ---
                if st.session_state.audio_buffer:
                    file_name = safe_filename(f"{yt.title}.mp3")
                    st.download_button(
                        label="💾 Save Audio File (.mp3)",
                        data=st.session_state.audio_buffer,
                        file_name=file_name,
                        mime="audio/mpeg"
                    )