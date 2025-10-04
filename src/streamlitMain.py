import streamlit as st
from src.main import YoutubeDownloader

st.title(":zap: YouTube Video Downloader")

option = ['Video' , 'PlayList' , 'Audio']
# selection (Default: Video)
selection = st.pills("Select Download:" , option , default='Video')
if selection == "Video":
    url = st.text_input("Enter YouTube Video URL")
    if url:
        downloader = YoutubeDownloader(url)
        selected_quality = downloader.get_available_qualities()
        quality = st.selectbox("Select Quality", selected_quality)
        downloader.quality = quality

    if st.button("Download Video"):
        if url:
            downloader = YoutubeDownloader(url)
            selected_quality = downloader.get_available_qualities()
            quality = st.selectbox("Select Quality", selected_quality)
            downloader.quality = quality
            file_path = downloader.Download()
            if file_path:
                with open(file_path, "rb") as file:
                    st.download_button(
                        label="⬇️ Download Video",
                        data=file,
                        file_name=file_path.split("/")[-1],
                        mime="video/mp4"
                    )
            # Download failed
            else:
                st.error("❌ Failed to download the video. Please check the URL and try again.")
        else:
            st.error("Please enter a valid YouTube URL.")

    # Download caption
    # if st.button("Download Caption"):
    #     if url:
    #         downloader = YoutubeDownloader(url)
    #         file_path = downloader.DownloadCaptions()
    #         if file_path:
    #             with open(file_path, "rb") as file:
    #                 st.download_button(
    #                     label="⬇️ Download Captions",
    #                     data=file,
    #                     file_name=file_path.split("/")[-1],
    #                     mime="text/vtt"
    #                 )
    #         else:
    #             st.error("❌ Failed to download captions. Please check if captions are available for this video.")
    #     else:
    #         st.error("Please enter a valid YouTube URL.")

# PlayList
if selection == "PlayList":
    url = st.text_input("Enter YouTube PlayList URL")
    quality = st.selectbox("Select Quality", ('highest', '1080p', '720p', '480p', '360p'))

    if st.button("Download"):
        if url:
            downloader = YoutubeDownloader(url, quality=quality)
            file_path = downloader.DownloadPlaylist()
            if file_path:
                with open(file_path, "rb") as file:
                    st.download_button(
                        label="⬇️ Download PlayList",
                        data=file,
                        file_name=file_path.split("/")[-1],
                        mime="application/zip"
                    )
            else:
                st.error("❌ Failed to download the playlist. Please check the URL and try again.")
        else:
            st.error("Please enter a valid YouTube URL.")
    # Download captions
    # if st.button("Download Captions"):
    #     if url:
    #         downloader = YoutubeDownloader(url)
    #         file_path = downloader.DownloadCaptions()
    #         if file_path:
    #             with open(file_path, "rb") as file:
    #                 st.download_button(
    #                     label="⬇️ Download Captions",
    #                     data=file,
    #                     file_name=file_path.split("/")[-1],
    #                     mime="text/vtt"
    #                 )
    #         else:
    #             st.error("❌ Failed to download captions. Please check if captions are available for this playlist.")
    #     else:
    #         st.error("Please enter a valid YouTube URL.")


# Audio
if selection == "Audio":
    url = st.text_input("Enter YouTube Audio URL")
    quality = st.selectbox("Select Quality", ('highest', '128kbps', '64kbps'))
    if st.button("Download"):
        if url:
            downloader = YoutubeDownloader(url, quality=quality)
            file_path = downloader.DownloadAudio()
            if file_path:
                with open(file_path, "rb") as file:
                    st.download_button(
                        label="⬇️ Download Audio",
                        data=file,
                        file_name=file_path.split("/")[-1],
                        mime="audio/mp3"
                    )
            else:
                st.error("❌ Failed to download the audio. Please check the URL and try again.")
        else:
            st.error("Please enter a valid YouTube URL.")
