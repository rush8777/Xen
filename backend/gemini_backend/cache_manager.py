import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict
from . import config


class CacheManager:
    def __init__(self):
        self.cache_file = config.CACHE_FILE
        self.cache_data = self._load_cache()
    
    def _load_cache(self) -> Dict:
        """Load cache from JSON file"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}
    
    def _save_cache(self):
        """Save cache to JSON file"""
        with open(self.cache_file, 'w') as f:
            json.dump(self.cache_data, f, indent=2)
    
    def calculate_video_hash(self, video_path: Path) -> str:
        """Calculate SHA256 hash of video file"""
        sha256_hash = hashlib.sha256()
        with open(video_path, "rb") as f:
            # Read in chunks to handle large files
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def get_cached_reference(self, video_hash: str) -> Optional[Dict]:
        """Get cached Gemini reference if exists and not expired"""
        if video_hash not in self.cache_data:
            return None
        
        cache_entry = self.cache_data[video_hash]
        expires_at = datetime.fromisoformat(cache_entry['expires_at'])
        
        # Check if expired
        if datetime.now() > expires_at:
            # Remove expired entry
            del self.cache_data[video_hash]
            self._save_cache()
            return None
        
        return cache_entry
    
    def save_cache_entry(self, video_hash: str, gemini_file_uri: str, 
                        duration: float, original_filename: str):
        """Save new cache entry"""
        now = datetime.now()
        expires_at = now + timedelta(hours=config.CACHE_EXPIRY_HOURS)
        
        self.cache_data[video_hash] = {
            "gemini_file_uri": gemini_file_uri,
            "uploaded_at": now.isoformat(),
            "duration": duration,
            "expires_at": expires_at.isoformat(),
            "original_filename": original_filename
        }
        self._save_cache()
    
    def cleanup_expired_cache(self):
        """Remove all expired cache entries"""
        now = datetime.now()
        expired_keys = []
        
        for video_hash, entry in self.cache_data.items():
            expires_at = datetime.fromisoformat(entry['expires_at'])
            if now > expires_at:
                expired_keys.append(video_hash)
        
        for key in expired_keys:
            del self.cache_data[key]
        
        if expired_keys:
            self._save_cache()
        
        return len(expired_keys)


# Global cache manager instance
cache_manager = CacheManager()
