import streamlit as st
from src.main import YoutubeDownloader
from src.Safe import safe_filename
import time

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
if 'playlist_buffer' not in st.session_state:
    st.session_state.playlist_buffer = None
if 'current_url' not in st.session_state:
    st.session_state.current_url = ""

# --- Helper function to reset state on new URL ---
def reset_state_on_new_url(new_url):
    if new_url != st.session_state.current_url:
        st.session_state.downloader = None
        st.session_state.video_buffer = None
        st.session_state.audio_buffer = None
        st.session_state.playlist_buffer = None
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
                    st.session_state.downloader = YoutubeDownloader(url)
                except Exception as e:
                    st.error(f"❌ Failed to load video. Check URL or try again. Error: {e}")
                    st.session_state.downloader = None
        
        # --- Display Video Info and Download Options ---
        if st.session_state.downloader and st.session_state.downloader.yt:
            yt = st.session_state.downloader.yt
            
            col1, col2 = st.columns([1, 2])
            with col1:
                st.image(yt.thumbnail_url, use_column_width=True)
            with col2:
                st.subheader(yt.title)
                st.caption(f"by {yt.author} | {yt.views:,} views | Length: {time.strftime('%H:%M:%S', time.gmtime(yt.length))}")

            st.divider()

            # --- Quality Selection ---
            video_qualities = st.session_state.downloader.get_video_qualities()
            if not video_qualities:
                st.warning("No MP4 video streams found.")
            else:
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

                # --- Direct Link (IDM) Expander ---
                with st.expander("🔗 Get Direct Link (for IDM, etc.)"):
                    if st.button("Generate Direct Link", key="video_direct_link_button"):
                        with st.spinner("Getting link..."):
                            link, error = st.session_state.downloader.get_direct_link(quality=quality, only_audio=False)
                            if link:
                                st.success("✅ Link generated! Copy this into your download manager.")
                                st.code(link)
                            else:
                                st.error(f"❌ Could not get link: {error}")

# ------------------------------------------
# 📂 PLAYLIST TAB
# ------------------------------------------
with tab2:
    st.header("Playlist Download")
    pl_url = st.text_input("Enter YouTube Playlist URL", key="playlist_url_input")
    
    reset_state_on_new_url(pl_url)

    if pl_url:
        if not st.session_state.downloader:
            with st.spinner("Loading playlist info..."):
                try:
                    st.session_state.downloader = YoutubeDownloader(pl_url)
                except Exception as e:
                    st.error(f"❌ Failed to load playlist. Check URL or try again. Error: {e}")
                    st.session_state.downloader = None
        
        # --- Display Playlist Info and Download Options ---
        if st.session_state.downloader and st.session_state.downloader.pl:
            pl = st.session_state.downloader.pl
            yt_info = st.session_state.downloader.yt # Get info from first video
            
            st.subheader(pl.title)
            st.caption(f"by {yt_info.author} | {pl.length} videos")
            st.divider()

            col1, col2 = st.columns(2)
            with col1:
                # Use first video's qualities as a proxy
                video_qualities = st.session_state.downloader.get_video_qualities()
                quality = st.selectbox("Select Video Quality", video_qualities, key="playlist_quality_select")
            with col2:
                download_type = st.radio("Download as:", ("Video", "Audio"), horizontal=True, key="playlist_type_radio")

            if st.button("⬇️ Download Playlist (.zip)", key="playlist_download_button"):
                st.session_state.playlist_buffer = None # Clear old buffer
                progress_bar = st.progress(0, text="Starting playlist download...")
                with st.spinner("Downloading playlist... This may take a while."):
                    try:
                        is_audio = (download_type == "Audio")
                        buffer = st.session_state.downloader.DownloadPlaylist(
                            quality=quality,
                            only_audio=is_audio,
                            st_progress_bar=progress_bar
                        )
                        st.session_state.playlist_buffer = buffer
                    except Exception as e:
                        st.error(f"❌ Playlist download failed: {e}")
                        progress_bar.empty()

            # --- Show Save Button if buffer is ready ---
            if st.session_state.playlist_buffer:
                file_name = safe_filename(f"{pl.title}.zip")
                st.download_button(
                    label="💾 Save Playlist ZIP",
                    data=st.session_state.playlist_buffer,
                    file_name=file_name,
                    mime="application/zip"
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
                    st.session_state.downloader = YoutubeDownloader(audio_url)
                except Exception as e:
                    st.error(f"❌ Failed to load video. Check URL or try again. Error: {e}")
                    st.session_state.downloader = None

        # --- Display Video Info and Download Options ---
        if st.session_state.downloader and st.session_state.downloader.yt:
            yt = st.session_state.downloader.yt
            
            col1, col2 = st.columns([1, 2])
            with col1:
                st.image(yt.thumbnail_url, use_column_width=True)
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

                # --- Direct Link (IDM) Expander ---
                with st.expander("🔗 Get Direct Link (for IDM, etc.)"):
                    if st.button("Generate Direct Link", key="audio_direct_link_button"):
                        with st.spinner("Getting link..."):
                            link, error = st.session_state.downloader.get_direct_link(quality=audio_quality, only_audio=True)
                            if link:
                                st.success("✅ Link generated! Copy this into your download manager.")
                                st.code(link)
                            else:
                                st.error(f"❌ Could not get link: {error}")