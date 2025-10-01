import streamlit as st
from src.main import YoutubeDownloader

st.title(":zap: YouTube Video Downloader")

url = st.text_input("Enter YouTube Video URL")
quality = st.selectbox("Select Quality", ('highest', '1080p', '720p', '480p', '360p'))

if st.button("Download"):
    if url:
        downloader = YoutubeDownloader(url, quality=quality)
        file_path = downloader.Download()
        if file_path:
            with open(file_path, "rb") as file:
                st.download_button(
                    label="Download Video",
                    data=file,
                    file_name=file_path.split("/")[-1],
                    mime="video/mp4"
                )
        else:
            st.error("Failed to download the video. Please check the URL and try again.")
    else:
        st.error("Please enter a valid YouTube URL.")
