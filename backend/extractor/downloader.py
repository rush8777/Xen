import yt_dlp
import os
from pathlib import Path
from typing import Dict, Optional
from ..config import settings


class VideoDownloader:
    """
    Video downloader service using yt-dlp
    Supports YouTube, Facebook, TikTok, Instagram, and many other platforms
    """
    
    def __init__(self):
        self.download_dir = Path(settings.DOWNLOAD_DIR)
        self.download_dir.mkdir(exist_ok=True)
        
    def get_info(self, url: str) -> Dict:
        """
        Get video information without downloading
        
        Args:
            url: Video URL
            
        Returns:
            Dictionary containing video metadata
        """
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info
    
    def download(
        self,
        url: str,
        quality: str = "best",
        audio_only: bool = False,
        output_filename: Optional[str] = None
    ) -> str:
        """
        Download video and return filepath
        
        Args:
            url: Video URL
            quality: Video quality (best, 1080p, 720p, 480p, 360p)
            audio_only: If True, extract audio only
            output_filename: Optional custom output filename (without extension)
            
        Returns:
            Path to downloaded file
        """
        
        # Quality format mapping for video
        quality_map = {
            "best": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "1080p": "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/best",
            "720p": "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best",
            "480p": "bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480][ext=mp4]/best",
            "360p": "bestvideo[height<=360][ext=mp4]+bestaudio[ext=m4a]/best[height<=360][ext=mp4]/best",
        }
        
        # Determine output template
        if output_filename:
            outtmpl = str(self.download_dir / f"{output_filename}.%(ext)s")
        else:
            outtmpl = str(self.download_dir / '%(title)s.%(ext)s')
        
        # Base options
        ydl_opts = {
            'format': 'bestaudio/best' if audio_only else quality_map.get(quality, quality_map["best"]),
            'outtmpl': outtmpl,
            'quiet': False,
            'no_warnings': False,
            'progress_hooks': [self._progress_hook],
            'socket_timeout': settings.DOWNLOAD_TIMEOUT_SECONDS,  # 5 minutes
        }
        
        # Add audio extraction post-processor if needed
        if audio_only:
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
            # Ensure we have ffmpeg
            ydl_opts['prefer_ffmpeg'] = True
        
        # Download the video
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            
            # Get the downloaded filename
            filename = ydl.prepare_filename(info)
            
            # Handle audio extraction filename change
            if audio_only:
                # yt-dlp changes extension to .mp3 after extraction
                filename = filename.rsplit('.', 1)[0] + '.mp3'
            
            return filename
    
    def _progress_hook(self, d):
        """
        Hook to track download progress
        """
        if d['status'] == 'downloading':
            downloaded = d.get('downloaded_bytes', 0)
            total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
            
            if total > 0:
                percent = (downloaded / total) * 100
                print(f"\rDownloading: {percent:.1f}%", end='', flush=True)
        elif d['status'] == 'finished':
            print(f"\n✓ Download finished: {d['filename']}")
    
    def get_supported_platforms(self) -> list:
        """
        Get list of supported platforms
        Note: yt-dlp supports 1000+ sites, here are the main ones
        """
        return [
            "YouTube",
            "Facebook",
            "Instagram",
            "TikTok",
            "Twitter/X",
            "Vimeo",
            "Dailymotion",
            "Reddit",
            "Twitch",
            "LinkedIn",
            # ... and many more
        ]
