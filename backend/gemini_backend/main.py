#!/usr/bin/env python3
"""
Video Analyzer CLI
Analyze videos using Google Gemini AI with interval-based descriptions
"""

import argparse
import asyncio
import sys
from pathlib import Path
import uuid

try:
    from .cache_manager import cache_manager
    from .video_processor import get_video_duration, generate_timestamps, save_descriptions
    from .gemini_client import (
        upload_video_to_gemini,
        analyze_video_intervals,
        client,
        SYSTEM_INSTRUCTIONS,
    )
    from google.genai import types
    from . import config
except ImportError:  # pragma: no cover
    from cache_manager import cache_manager
    from video_processor import get_video_duration, generate_timestamps, save_descriptions
    from gemini_client import (
        upload_video_to_gemini,
        analyze_video_intervals,
        client,
        SYSTEM_INSTRUCTIONS,
    )
    from google.genai import types
    import config


class VideoAnalyzer:
    """Video analyzer with proper cached content support"""
    
    def __init__(self):
        self.jobs = {}
    
    def create_job(self, video_path: Path) -> str:
        """Create a new analysis job"""
        job_id = str(uuid.uuid4())
        
        # Calculate video hash
        print(f"📊 Calculating video hash...")
        video_hash = cache_manager.calculate_video_hash(video_path)
        
        # Check cache
        cached_entry = cache_manager.get_cached_reference(video_hash)
        
        duration = get_video_duration(video_path)
        print(f"   Duration: {duration:.2f}s")
        
        if cached_entry:
            # Cache hit - use existing reference
            print(f"✅ Cache hit! Using existing Gemini reference")
            print(f"   Original file: {cached_entry['original_filename']}")
            
            self.jobs[job_id] = {
                "filename": video_path.name,
                "video_path": video_path,
                "cached_content_name": cached_entry.get('cached_content_name'),
                "duration": duration,
                "video_hash": video_hash,
                "status": "cached",
                "cache_hit": True
            }
        else:
            # Cache miss - need to upload and create cache
            print(f"⚠️  Cache miss - will upload to Gemini")
            
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
        """Analyze a video job using proper cached content"""
        if job_id not in self.jobs:
            raise ValueError(f"Job ID not found: {job_id}")
        
        job = self.jobs[job_id]
        
        # Create or retrieve cached content
        if not job.get('cache_hit', False) or not job.get('cached_content_name'):
            try:
                print(f"\n📤 Uploading video to Gemini...")
                job['status'] = "uploading"
                
                # Upload video file
                gemini_file_name = await upload_video_to_gemini(job['video_path'])
                video_file = client.files.get(name=gemini_file_name)
                
                # Wait for file to be ready
                while getattr(video_file.state, "name", None) == "PROCESSING":
                    print("   Processing video...")
                    await asyncio.sleep(2.5)
                    video_file = client.files.get(name=video_file.name)
                
                if getattr(video_file.state, "name", None) != "ACTIVE":
                    raise RuntimeError(
                        f"Video file is not ACTIVE: {getattr(video_file.state, 'name', video_file.state)}"
                    )
                
                print(f"✅ Video uploaded successfully!")
                print(f"   File: {video_file.name}")
                
                # Create cached content with system instructions and video
                print(f"\n🔄 Creating cached content...")
                
                cache = client.caches.create(
                    model="models/gemini-2.5-flash",
                    config=types.CreateCachedContentConfig(
                        display_name=f"video-analysis-{job['video_hash'][:12]}",
                        system_instruction=SYSTEM_INSTRUCTIONS,
                        contents=[video_file],
                        ttl="3600s",  # 1 hour cache
                    ),
                )
                
                print(f"✅ Cached content created!")
                print(f"   Cache name: {cache.name}")
                
                job['cached_content_name'] = cache.name
                job['gemini_file_name'] = video_file.name
                
                # Save to cache manager
                cache_manager.save_cache_entry(
                    job['video_hash'],
                    cache.name,  # Save the cached content name
                    job['duration'],
                    job['filename']
                )
                
                job['status'] = "cached"
                
            except Exception as e:
                job['status'] = "upload_failed"
                raise Exception(f"Upload/cache creation failed: {str(e)}")
        
        # Generate intervals
        intervals = generate_timestamps(job['duration'])
        print(f"\n🎬 Analyzing {len(intervals)} intervals (5-second chunks)...")
        print(f"   Total intervals: {len(intervals)}")
        print(f"   Estimated time: ~{len(intervals) * 2}s (with concurrency)")
        
        try:
            job['status'] = "analyzing"
            
            # Analyze all intervals concurrently using cached content
            descriptions = await analyze_video_intervals(
                job['cached_content_name'],  # Pass cached content name
                intervals
            )
            
            # Save results
            output_path = await save_descriptions(job_id, descriptions)
            
            job['status'] = "completed"
            job['output_path'] = output_path
            
            print(f"\n✅ Analysis completed!")
            print(f"   Intervals analyzed: {len(descriptions)}")
            print(f"   Output file: {output_path}")
            
            return output_path
        
        except Exception as e:
            job['status'] = "analysis_failed"
            raise Exception(f"Analysis failed: {str(e)}")
    
    def get_job_status(self, job_id: str) -> dict:
        """Get status of a job"""
        if job_id not in self.jobs:
            raise ValueError(f"Job ID not found: {job_id}")
        
        job = self.jobs[job_id]
        return {
            "job_id": job_id,
            "filename": job['filename'],
            "status": job['status'],
            "duration": job.get('duration'),
            "cache_hit": job.get('cache_hit', False)
        }


async def analyze_video_command(video_path: Path, output: str = None):
    """Analyze a video file"""
    if not video_path.exists():
        print(f"❌ Error: Video file not found: {video_path}", file=sys.stderr)
        sys.exit(1)
    
    if not video_path.suffix.lower() in ['.mp4', '.avi', '.mov', '.mkv', '.webm']:
        print(f"❌ Error: Invalid video format. Supported: mp4, avi, mov, mkv, webm", file=sys.stderr)
        sys.exit(1)
    
    print("=" * 70)
    print(f"🎥 Video Analyzer - Powered by Google Gemini")
    print("=" * 70)
    print(f"\n📁 Video: {video_path.name}")
    
    # Create analyzer
    analyzer = VideoAnalyzer()
    
    # Create job
    job_id = analyzer.create_job(video_path)
    print(f"🆔 Job ID: {job_id}")
    
    # Analyze
    try:
        output_path = await analyzer.analyze_job(job_id)
        
        # Display results
        print("\n" + "=" * 70)
        print("📄 RESULTS")
        print("=" * 70)
        
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # Show first 2000 characters
            if len(content) > 2000:
                print(content[:2000])
                print("\n... [truncated, see output file for full results] ...")
            else:
                print(content)
        
        print("=" * 70)
        print(f"💾 Results saved to: {output_path}")
        
        # Copy to custom output if specified
        if output:
            import shutil
            output_file = Path(output)
            shutil.copy(output_path, output_file)
            print(f"💾 Results also saved to: {output_file}")
        
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


def cleanup_cache_command():
    """Clean up expired cache entries"""
    print("🧹 Cleaning up expired cache entries...")
    cleaned = cache_manager.cleanup_expired_cache()
    print(f"✅ Cleaned up {cleaned} expired cache entries")


def list_cache_command():
    """List all cache entries"""
    if not cache_manager.cache_data:
        print("🔭 Cache is empty")
        return
    
    print("=" * 70)
    print("CACHE ENTRIES")
    print("=" * 70)
    
    from datetime import datetime
    
    for i, (video_hash, entry) in enumerate(cache_manager.cache_data.items(), 1):
        print(f"\n{i}. Hash: {video_hash[:16]}...")
        print(f"   Filename: {entry['original_filename']}")
        print(f"   Duration: {entry['duration']:.2f}s")
        print(f"   Uploaded: {entry['uploaded_at']}")
        print(f"   Expires: {entry['expires_at']}")
        
        # Check if expired
        expires_at = datetime.fromisoformat(entry['expires_at'])
        if datetime.now() > expires_at:
            print(f"   Status: ⚠️  EXPIRED")
        else:
            time_left = expires_at - datetime.now()
            hours_left = time_left.total_seconds() / 3600
            print(f"   Status: ✅ Active ({hours_left:.1f}h remaining)")
    
    print("\n" + "=" * 70)
    print(f"Total entries: {len(cache_manager.cache_data)}")
    print("=" * 70)


def info_command():
    """Show system information"""
    print("=" * 70)
    print("VIDEO ANALYZER - SYSTEM INFO")
    print("=" * 70)
    print(f"\n📂 Base directory: {config.BASE_DIR}")
    print(f"📤 Upload directory: {config.UPLOAD_DIR}")
    print(f"📥 Output directory: {config.OUTPUT_DIR}")
    print(f"💾 Cache directory: {config.CACHE_DIR}")
    print(f"\n⚙️  Interval seconds: {config.INTERVAL_SECONDS}s")
    print(f"🔄 Max concurrent requests: {config.MAX_CONCURRENT_REQUESTS}")
    print(f"⏰ Cache expiry: {config.CACHE_EXPIRY_HOURS}h")
    print(f"\n🔑 API Key configured: {'Yes' if config.GEMINI_API_KEY else 'No'}")
    
    if not config.GEMINI_API_KEY:
        print("\n⚠️  WARNING: GEMINI_API_KEY not set!")
        print("   Set it with: export GEMINI_API_KEY='your-api-key'")
    
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(
        description='Video Analyzer - Analyze videos using Google Gemini AI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze a video
  python main.py analyze video.mp4
  
  # Analyze with custom output
  python main.py analyze video.mp4 --output results.txt
  
  # List cache entries
  python main.py cache-list
  
  # Clean up expired cache
  python main.py cache-cleanup
  
  # Show system info
  python main.py info

Environment Variables:
  GEMINI_API_KEY    Google Gemini API key (required)

The analyzer processes videos in 5-second intervals and provides
objective visual descriptions for each interval.
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze a video file')
    analyze_parser.add_argument('video', type=Path, help='Path to video file')
    analyze_parser.add_argument(
        '--output', '-o',
        help='Custom output file path'
    )
    
    # Cache commands
    cache_list_parser = subparsers.add_parser('cache-list', help='List cached videos')
    cache_cleanup_parser = subparsers.add_parser('cache-cleanup', help='Clean up expired cache entries')
    
    # Info command
    info_parser = subparsers.add_parser('info', help='Show system information')
    
    args = parser.parse_args()
    
    # Show help if no command provided
    if not args.command:
        parser.print_help()
        sys.exit(0)
    
    # Execute command
    if args.command == 'analyze':
        asyncio.run(analyze_video_command(args.video, args.output))
    
    elif args.command == 'cache-list':
        list_cache_command()
    
    elif args.command == 'cache-cleanup':
        cleanup_cache_command()
    
    elif args.command == 'info':
        info_command()


if __name__ == "__main__":
    main()