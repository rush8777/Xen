"""
Gemini Video Analyzer Module
Wrapper for direct integration without CLI interface
"""

import asyncio
from pathlib import Path
import uuid
from typing import Dict

# Import from gemini-cli modules
import sys
import os

BASE_DIR = (
    os.path.dirname(os.path.abspath(__file__))
    if "__file__" in globals()
    else os.getcwd()
)

sys.path.append(os.path.dirname(BASE_DIR))



# Add gemini-cli to path if needed
# sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'gemini-cli'))

from ..gemini_backend.cache_manager import cache_manager
from ..gemini_backend import config
from ..gemini_backend.video_processor import get_video_duration, generate_timestamps, save_descriptions
from ..gemini_backend.gemini_client import (
    upload_video_to_gemini,
    analyze_video_intervals,
    client,
    SYSTEM_INSTRUCTIONS,
)

from google.genai import types


class VideoAnalyzer:
    """
    Video analyzer for direct integration
    Provides programmatic interface to Gemini video analysis
    """
    
    def __init__(self):
        self.jobs: Dict = {}
    
    def create_job(self, video_path: Path) -> str:
        """
        Create a new analysis job
        
        Args:
            video_path: Path to video file
            
        Returns:
            job_id: Unique identifier for this job
        """
        job_id = str(uuid.uuid4())
        
        # Calculate video hash
        video_hash = cache_manager.calculate_video_hash(video_path)
        
        # Check cache
        cached_entry = cache_manager.get_cached_reference(video_hash)
        
        if cached_entry:
            # Cache hit - use existing reference
            self.jobs[job_id] = {
                "filename": video_path.name,
                "video_path": video_path,
                "cached_content_name": cached_entry.get("cached_content_name"),
                "duration": cached_entry["duration"],
                "video_hash": video_hash,
                "status": "cached",
                "cache_hit": bool(cached_entry.get("cached_content_name")),
            }
        else:
            # Cache miss - need to upload
            duration = get_video_duration(video_path)
            
            self.jobs[job_id] = {
                "filename": video_path.name,
                "video_path": video_path,
                "duration": duration,
                "video_hash": video_hash,
                "status": "pending_upload",
                "cache_hit": False
            }
        
        return job_id
    
    async def analyze_job(self, job_id: str) -> Path:
        """
        Analyze a video job
        
        Args:
            job_id: Job identifier from create_job()
            
        Returns:
            output_path: Path to results file
            
        Raises:
            ValueError: If job_id not found
            Exception: If upload or analysis fails
        """
        if job_id not in self.jobs:
            raise ValueError(f"Job ID not found: {job_id}")
        
        job = self.jobs[job_id]
        
        # Upload + create cached content if not cached
        if not job.get("cache_hit", False) or not job.get("cached_content_name"):
            try:
                job['status'] = "uploading"

                gemini_file_name = await upload_video_to_gemini(job["video_path"])
                video_file = client.files.get(name=gemini_file_name)

                while getattr(video_file.state, "name", None) == "PROCESSING":
                    await asyncio.sleep(2.5)
                    video_file = client.files.get(name=video_file.name)

                if getattr(video_file.state, "name", None) != "ACTIVE":
                    raise RuntimeError(
                        f"Video file is not ACTIVE: {getattr(video_file.state, 'name', video_file.state)}"
                    )

                cache = client.caches.create(
                    model="models/gemini-2.5-flash",
                    config=types.CreateCachedContentConfig(
                        display_name=f"video-analysis-{job['video_hash'][:12]}",
                        system_instruction=SYSTEM_INSTRUCTIONS,
                        contents=[video_file],
                        ttl=f"{int(config.CACHE_EXPIRY_HOURS * 3600)}s",
                    ),
                )

                job["cached_content_name"] = cache.name

                # Save to cache
                cache_manager.save_cache_entry(
                    job['video_hash'],
                    job["cached_content_name"],
                    job['duration'],
                    job['filename'],
                    gemini_file_name=video_file.name,
                )
                
                job['status'] = "cached"
            except Exception as e:
                job['status'] = "upload_failed"
                raise Exception(f"Upload failed: {str(e)}")
        
        # Generate intervals
        intervals = generate_timestamps(job['duration'])
        
        try:
            job['status'] = "analyzing"
            
            # Analyze all intervals concurrently
            descriptions = await analyze_video_intervals(job["cached_content_name"], intervals)
            
            # Save results
            output_path = await save_descriptions(job_id, descriptions)
            
            job['status'] = "completed"
            job['output_path'] = output_path
            
            # Clean up video file after successful analysis
            try:
                if job['video_path'].exists():
                    job['video_path'].unlink()
            except:
                pass  # Best effort cleanup
            
            return output_path
        
        except Exception as e:
            job['status'] = "analysis_failed"
            raise Exception(f"Analysis failed: {str(e)}")
    
    def get_job_status(self, job_id: str) -> dict:
        """
        Get status of a job
        
        Args:
            job_id: Job identifier
            
        Returns:
            Dictionary with job status information
            
        Raises:
            ValueError: If job_id not found
        """
        if job_id not in self.jobs:
            raise ValueError(f"Job ID not found: {job_id}")
        
        job = self.jobs[job_id]
        return {
            "job_id": job_id,
            "filename": job['filename'],
            "status": job['status'],
            "duration": job.get('duration'),
            "cache_hit": job.get('cache_hit', False),
            "output_path": str(job.get('output_path', '')) if job.get('output_path') else None
        }
    
    def get_job_results(self, job_id: str) -> str:
        """
        Get analysis results as text
        
        Args:
            job_id: Job identifier
            
        Returns:
            Results text with timestamped descriptions
            
        Raises:
            ValueError: If job not found or not completed
        """
        if job_id not in self.jobs:
            raise ValueError(f"Job ID not found: {job_id}")
        
        job = self.jobs[job_id]
        
        if job['status'] != "completed":
            raise ValueError(f"Analysis not completed. Current status: {job['status']}")
        
        output_path = job.get('output_path')
        if not output_path or not output_path.exists():
            raise ValueError("Results file not found")
        
        with open(output_path, 'r', encoding='utf-8') as f:
            return f.read()