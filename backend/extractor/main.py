#!/usr/bin/env python3
"""
Video Downloader CLI
Download videos from YouTube, Facebook, TikTok, Instagram, and many other platforms
"""

import argparse
import sys
import os
from pathlib import Path
from downloader import VideoDownloader
from config import settings


def format_duration(seconds):
    """Format duration in seconds to readable format"""
    if not seconds:
        return "Unknown"
    
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"


def format_filesize(bytes_size):
    """Format file size to human readable format"""
    if not bytes_size:
        return "Unknown"
    
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} TB"


def get_info_command(downloader, url):
    """Get and display video information"""
    print(f"\n🔍 Fetching video information...\n")
    
    try:
        info = downloader.get_info(url)
        
        print("=" * 70)
        print(f"Title:     {info.get('title', 'Unknown')}")
        print(f"Platform:  {info.get('extractor', 'Unknown')}")
        print(f"Uploader:  {info.get('uploader', 'Unknown')}")
        print(f"Duration:  {format_duration(info.get('duration'))}")
        print(f"Views:     {info.get('view_count', 'Unknown'):,}" if info.get('view_count') else "Views:     Unknown")
        print("=" * 70)
        
        # Show available formats
        if info.get('formats'):
            print("\n📊 Available Formats (showing top 10):")
            print("-" * 70)
            
            formats_shown = 0
            for f in info.get('formats', []):
                if formats_shown >= 10:
                    break
                
                format_id = f.get('format_id', 'N/A')
                resolution = f.get('resolution', 'N/A')
                ext = f.get('ext', 'N/A')
                quality = f.get('format_note', 'N/A')
                filesize = format_filesize(f.get('filesize')) if f.get('filesize') else 'N/A'
                
                print(f"{format_id:10} | {resolution:15} | {ext:6} | {quality:15} | {filesize}")
                formats_shown += 1
            
            print("-" * 70)
        
        print()
        
    except Exception as e:
        print(f"❌ Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


def download_command(downloader, url, quality, audio_only, output):
    """Download video"""
    print(f"\n📥 Starting download...\n")
    
    try:
        filepath = downloader.download(
            url=url,
            quality=quality,
            audio_only=audio_only,
            output_filename=output
        )
        
        if os.path.exists(filepath):
            file_size = os.path.getsize(filepath)
            print(f"\n✅ Download completed successfully!")
            print(f"📁 File: {filepath}")
            print(f"📊 Size: {format_filesize(file_size)}")
        else:
            print(f"❌ Download completed but file not found", file=sys.stderr)
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Download failed: {str(e)}", file=sys.stderr)
        sys.exit(1)


def list_downloads_command(downloader):
    """List all downloaded files"""
    download_dir = Path(settings.DOWNLOAD_DIR)
    
    if not download_dir.exists():
        print(f"📁 Download directory doesn't exist: {download_dir}")
        return
    
    files = []
    for file_path in download_dir.glob("*"):
        if file_path.is_file() and file_path.name != '.gitkeep':
            stat = file_path.stat()
            files.append({
                'name': file_path.name,
                'size': stat.st_size,
                'path': str(file_path)
            })
    
    if not files:
        print(f"📁 No files in download directory: {download_dir}")
        return
    
    # Sort by name
    files.sort(key=lambda x: x['name'])
    
    print(f"\n📁 Downloaded files in {download_dir}:")
    print("=" * 70)
    
    for i, file in enumerate(files, 1):
        print(f"{i}. {file['name']}")
        print(f"   Size: {format_filesize(file['size'])}")
        print(f"   Path: {file['path']}")
        print()
    
    print(f"Total files: {len(files)}")
    print("=" * 70)


def delete_command(filename):
    """Delete a downloaded file"""
    file_path = Path(settings.DOWNLOAD_DIR) / filename
    
    if not file_path.exists():
        print(f"❌ File not found: {filename}", file=sys.stderr)
        sys.exit(1)
    
    # Security check - ensure file is within download directory
    if not str(file_path.resolve()).startswith(str(Path(settings.DOWNLOAD_DIR).resolve())):
        print(f"❌ Access denied: File is outside download directory", file=sys.stderr)
        sys.exit(1)
    
    try:
        file_path.unlink()
        print(f"✅ Deleted: {filename}")
    except Exception as e:
        print(f"❌ Failed to delete file: {str(e)}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description='Video Downloader - Download videos from various platforms',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Get video information
  python main.py info "https://www.youtube.com/watch?v=VIDEO_ID"
  
  # Download video in best quality
  python main.py download "https://www.youtube.com/watch?v=VIDEO_ID"
  
  # Download video in 720p
  python main.py download "https://www.youtube.com/watch?v=VIDEO_ID" --quality 720p
  
  # Download audio only
  python main.py download "https://www.youtube.com/watch?v=VIDEO_ID" --audio-only
  
  # Download with custom filename
  python main.py download "https://www.youtube.com/watch?v=VIDEO_ID" --output "my_video"
  
  # List downloaded files
  python main.py list
  
  # Delete a file
  python main.py delete "video_name.mp4"

Supported platforms: YouTube, Facebook, Instagram, TikTok, Twitter/X, Vimeo, 
Dailymotion, Reddit, Twitch, LinkedIn, and 1000+ more sites.
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Info command
    info_parser = subparsers.add_parser('info', help='Get video information without downloading')
    info_parser.add_argument('url', help='Video URL')
    
    # Download command
    download_parser = subparsers.add_parser('download', help='Download video')
    download_parser.add_argument('url', help='Video URL')
    download_parser.add_argument(
        '--quality', '-q',
        choices=['best', '1080p', '720p', '480p', '360p'],
        default='best',
        help='Video quality (default: best)'
    )
    download_parser.add_argument(
        '--audio-only', '-a',
        action='store_true',
        help='Download audio only (MP3)'
    )
    download_parser.add_argument(
        '--output', '-o',
        help='Custom output filename (without extension)'
    )
    
    # List command
    list_parser = subparsers.add_parser('list', help='List downloaded files')
    
    # Delete command
    delete_parser = subparsers.add_parser('delete', help='Delete a downloaded file')
    delete_parser.add_argument('filename', help='Filename to delete')
    
    args = parser.parse_args()
    
    # Show help if no command provided
    if not args.command:
        parser.print_help()
        sys.exit(0)
    
    # Initialize downloader
    downloader = VideoDownloader()
    
    # Execute command
    if args.command == 'info':
        get_info_command(downloader, args.url)
    
    elif args.command == 'download':
        download_command(downloader, args.url, args.quality, args.audio_only, args.output)
    
    elif args.command == 'list':
        list_downloads_command(downloader)
    
    elif args.command == 'delete':
        delete_command(args.filename)


if __name__ == "__main__":
    main()
