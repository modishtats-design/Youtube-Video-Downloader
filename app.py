import streamlit as st
import yt_dlp
import os
import tempfile
from pathlib import Path
import threading
import time
import zipfile
from datetime import datetime

# Configure page
st.set_page_config(
    page_title="YouTube Downloader",
    page_icon="🎥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #ff0000;
        text-align: center;
        margin-bottom: 2rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    
    .stButton > button {
        background: linear-gradient(90deg, #ff0000, #ff4444);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.5rem 1rem;
        font-weight: 600;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .stButton > button:hover {
        background: linear-gradient(90deg, #cc0000, #ff3333);
        transform: translateY(-2px);
        box-shadow: 0 6px 8px rgba(0, 0, 0, 0.15);
    }
    
    .video-info {
        background: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 4px solid #ff0000;
    }
    
    .download-section {
        background: white;
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

class StreamlitYouTubeDownloader:
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp()
        
    def get_video_info(self, url):
        """Extract video information without downloading"""
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return {
                    'title': info.get('title', 'Unknown'),
                    'duration': info.get('duration', 0),
                    'uploader': info.get('uploader', 'Unknown'),
                    'view_count': info.get('view_count', 0),
                    'description': info.get('description', '')[:200] + '...',
                    'thumbnail': info.get('thumbnail', ''),
                    'formats': info.get('formats', [])
                }
        except Exception as e:
            st.error(f"Error fetching video info: {str(e)}")
            return None
    
    def download_video(self, url, quality_option, include_subtitles=False):
        """Download video with specified options"""
        
        # Configure download options based on selection
        if quality_option == "Highest Quality":
            format_selector = 'best[ext=mp4]/best'
            filename_template = '%(title)s.%(ext)s'
        elif quality_option == "Audio Only (MP3)":
            format_selector = 'bestaudio/best'
            filename_template = '%(title)s.%(ext)s'
        elif quality_option.endswith('p'):
            height = quality_option.replace('p', '')
            format_selector = f'best[height<={height}][ext=mp4]/best[height<={height}]'
            filename_template = '%(title)s__{quality_option}.%(ext)s'
        else:
            format_selector = 'best[ext=mp4]/best'
            filename_template = '%(title)s.%(ext)s'
        
        ydl_opts = {
            'format': format_selector,
            'outtmpl': os.path.join(self.temp_dir, filename_template),
            'writeinfojson': False,
        }
        
        # Add subtitle options
        if include_subtitles and quality_option != "Audio Only (MP3)":
            ydl_opts.update({
                'writesubtitles': True,
                'writeautomaticsub': True,
                'subtitleslangs': ['en'],
            })
        
        # Add post-processing for audio
        if quality_option == "Audio Only (MP3)":
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
                
            # Find downloaded file
            downloaded_files = []
            for file in os.listdir(self.temp_dir):
                if file.endswith(('.mp4', '.mp3', '.webm', '.mkv')):
                    downloaded_files.append(os.path.join(self.temp_dir, file))
            
            return downloaded_files[0] if downloaded_files else None
            
        except Exception as e:
            st.error(f"Download failed: {str(e)}")
            return None

def format_duration(seconds):
    """Convert seconds to readable format"""
    if not seconds:
        return "Unknown"
    
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"

def format_views(view_count):
    """Format view count"""
    if not view_count:
        return "Unknown"
    
    if view_count >= 1_000_000:
        return f"{view_count / 1_000_000:.1f}M views"
    elif view_count >= 1_000:
        return f"{view_count / 1_000:.1f}K views"
    else:
        return f"{view_count} views"

def main():
    # Header
    st.markdown('<h1 class="main-header">🎥Tat_Nyama Video Downloader</h1>', unsafe_allow_html=True)
    
    # Initialize downloader
    if 'downloader' not in st.session_state:
        st.session_state.downloader = StreamlitYouTubeDownloader()
    
    # Sidebar for options
    with st.sidebar:
        st.markdown("### ⚙️ Download Options")
        
        quality_options = [
            "Highest Quality",
            "1080p",
            "720p",
            "480p",
            "360p",
            "Audio Only (MP3)"
        ]
        
        quality_choice = st.selectbox(
            "Select Quality:",
            quality_options,
            index=0
        )
        
        include_subtitles = st.checkbox("Include Subtitles", value=False)
        
        st.markdown("---")
        st.markdown("### 📋 Instructions")
        st.markdown("""
        1. Paste YouTube URL
        2. Click 'Get Video Info'
        3. Select quality options
        4. Click 'Download'
        5. Wait for download to complete
        """)
        
        st.markdown("---")
        st.markdown("### ℹ️ Supported Formats")
        st.markdown("""
        - **Video**: MP4, WebM
        - **Audio**: MP3 (192kbps)
        - **Subtitles**: SRT, VTT
        """)
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown('<div class="download-section">', unsafe_allow_html=True)
        st.markdown("### 🔗 Enter YouTube URL")
        
        url = st.text_input(
            "Paste YouTube video URL here:",
            placeholder="https://www.youtube.com/watch?v=...",
            help="Supports individual videos and playlist URLs"
        )
        
        col_info, col_download = st.columns(2)
        
        with col_info:
            get_info_button = st.button("📋 Get Video Info", use_container_width=True)
        
        with col_download:
            download_button = st.button("⬬ Download Video", use_container_width=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown("### 🎯 Quick Actions")
        
        if st.button("🗑️ Clear Cache", use_container_width=True):
            st.cache_data.clear()
            st.success("Cache cleared!")
        
        st.markdown("### 📊 Current Settings")
        st.info(f"""
        **Quality**: {quality_choice}
        **Subtitles**: {'Yes' if include_subtitles else 'No'}
        """)
    
    # Video info section
    if get_info_button and url:
        with st.spinner("Fetching video information..."):
            video_info = st.session_state.downloader.get_video_info(url)
            
            if video_info:
                st.markdown("---")
                st.markdown("### 📺 Video Information")
                
                col_thumb, col_details = st.columns([1, 2])
                
                with col_thumb:
                    if video_info['thumbnail']:
                        st.image(video_info['thumbnail'], use_container_width=True)
                
                with col_details:
                    st.markdown(f"""
                    <div class="video-info">
                    <h4>{video_info['title']}</h4>
                    <p><strong>Channel:</strong> {video_info['uploader']}</p>
                    <p><strong>Duration:</strong> {format_duration(video_info['duration'])}</p>
                    <p><strong>Views:</strong> {format_views(video_info['view_count'])}</p>
                    <p><strong>Description:</strong> {video_info['description']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Store video info in session state
                st.session_state.video_info = video_info
    
    # Download section
    if download_button and url:
        if 'video_info' not in st.session_state:
            st.warning("Please get video info first!")
        else:
            with st.spinner(f"Downloading in {quality_choice}..."):
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Simulate progress (since yt-dlp doesn't easily provide real-time progress in Streamlit)
                for i in range(100):
                    progress_bar.progress(i + 1)
                    status_text.text(f"Downloading... {i + 1}%")
                    time.sleep(0.1)
                
                downloaded_file = st.session_state.downloader.download_video(
                    url, quality_choice, include_subtitles
                )
                
                if downloaded_file and os.path.exists(downloaded_file):
                    st.success("✅ Download completed successfully!")
                    
                    # Provide download link
                    with open(downloaded_file, 'rb') as file:
                        file_data = file.read()
                        filename = os.path.basename(downloaded_file)
                        
                        st.download_button(
                            label=f"📥 Download {filename}",
                            data=file_data,
                            file_name=filename,
                            mime="application/octet-stream",
                            use_container_width=True
                        )
                    
                    # Show file info
                    file_size = os.path.getsize(downloaded_file) / (1024 * 1024)  # MB
                    st.info(f"File size: {file_size:.2f} MB")
                    
                else:
                    st.error("❌ Download failed. Please check the URL and try again.")

if __name__ == "__main__":
    main()