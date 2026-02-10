import os
from pathlib import Path
from typing import Optional


class Settings:
    """
    Application configuration settings
    These can be overridden by environment variables
    """
    
    def __init__(self):
        # Download settings
        self.DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR", "./downloads")
        self.MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "500"))
        
        # File retention (cleanup)
        self.FILE_RETENTION_HOURS = int(os.getenv("FILE_RETENTION_HOURS", "24"))
        
        # yt-dlp specific settings
        self.FFMPEG_PATH = os.getenv("FFMPEG_PATH", None)


# Create a global settings instance
settings = Settings()
