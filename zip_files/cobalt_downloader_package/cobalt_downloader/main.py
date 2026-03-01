#!/usr/bin/env python3
"""
Video Downloader CLI  (Cobalt backend)
Download videos from YouTube, Facebook, TikTok, Instagram, Twitter/X and more.

Usage is identical to the original yt-dlp-backed CLI.
"""

import argparse
import os
import sys
from pathlib import Path

# ── Swap: one-line change from the original ──────────────────────────────────
from .cobalt_downloader import VideoDownloader, warm_up_rotator
# ─────────────────────────────────────────────────────────────────────────────

try:
    from ..config import settings
    _DOWNLOAD_DIR = settings.DOWNLOAD_DIR
except Exception:
    _DOWNLOAD_DIR = "./downloads"


# ─────────────────────────────────────────────────────────────────────────────
# Formatters (unchanged from original)
# ─────────────────────────────────────────────────────────────────────────────

def format_duration(seconds):
    if not seconds:
        return "Unknown"
    hours   = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs    = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}" if hours else f"{minutes:02d}:{secs:02d}"


def format_filesize(bytes_size):
    if not bytes_size:
        return "Unknown"
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} TB"


# ─────────────────────────────────────────────────────────────────────────────
# Commands
# ─────────────────────────────────────────────────────────────────────────────

def get_info_command(downloader: VideoDownloader, url: str) -> None:
    print("\n🔍 Fetching video information…\n")
    try:
        info = downloader.get_info(url)
        print("=" * 70)
        print(f"Title:     {info.get('title', 'Unknown')}")
        print(f"Platform:  {info.get('extractor', 'Unknown')}")
        print(f"Uploader:  {info.get('uploader', 'Unknown')}")
        print(f"Duration:  {format_duration(info.get('duration'))}")
        if info.get('view_count'):
            print(f"Views:     {info['view_count']:,}")
        else:
            print("Views:     Unknown")
        print("=" * 70)

        formats = info.get('formats', [])
        if formats:
            print("\n📊 Available Formats:")
            print("-" * 70)
            for f in formats[:10]:
                print(
                    f"{f.get('format_id','N/A'):10} | "
                    f"{f.get('resolution','N/A'):15} | "
                    f"{f.get('ext','N/A'):6} | "
                    f"{f.get('format_note','N/A'):20} | "
                    f"{format_filesize(f.get('filesize'))}"
                )
            print("-" * 70)
        print()
    except Exception as exc:
        print(f"❌ Error: {exc}", file=sys.stderr)
        sys.exit(1)


def download_command(downloader: VideoDownloader, url: str, quality: str, audio_only: bool, output: str) -> None:
    print("\n📥 Starting download…\n")
    try:
        filepath = downloader.download(url=url, quality=quality, audio_only=audio_only, output_filename=output)
        if os.path.exists(filepath):
            size = os.path.getsize(filepath)
            print(f"\n✅ Download completed successfully!")
            print(f"📁 File: {filepath}")
            print(f"📊 Size: {format_filesize(size)}")
        else:
            print("❌ Download completed but file not found", file=sys.stderr)
            sys.exit(1)
    except Exception as exc:
        print(f"\n❌ Download failed: {exc}", file=sys.stderr)
        sys.exit(1)


def list_downloads_command(downloader: VideoDownloader) -> None:
    download_dir = Path(_DOWNLOAD_DIR)
    if not download_dir.exists():
        print(f"📁 Download directory doesn't exist: {download_dir}")
        return

    files = sorted(
        [
            {"name": p.name, "size": p.stat().st_size, "path": str(p)}
            for p in download_dir.glob("*")
            if p.is_file() and p.name != ".gitkeep"
        ],
        key=lambda x: x["name"],
    )

    if not files:
        print(f"📁 No files in download directory: {download_dir}")
        return

    print(f"\n📁 Downloaded files in {download_dir}:")
    print("=" * 70)
    for i, f in enumerate(files, 1):
        print(f"{i}. {f['name']}")
        print(f"   Size: {format_filesize(f['size'])}")
        print(f"   Path: {f['path']}\n")
    print(f"Total files: {len(files)}")
    print("=" * 70)


def delete_command(filename: str) -> None:
    file_path = Path(_DOWNLOAD_DIR) / filename
    if not file_path.exists():
        print(f"❌ File not found: {filename}", file=sys.stderr)
        sys.exit(1)
    if not str(file_path.resolve()).startswith(str(Path(_DOWNLOAD_DIR).resolve())):
        print("❌ Access denied: file is outside download directory", file=sys.stderr)
        sys.exit(1)
    try:
        file_path.unlink()
        print(f"✅ Deleted: {filename}")
    except Exception as exc:
        print(f"❌ Failed to delete: {exc}", file=sys.stderr)
        sys.exit(1)


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Video Downloader (Cobalt backend) — YouTube, Facebook, Instagram, TikTok, Twitter/X and more",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m video_downloader info  "https://www.youtube.com/watch?v=VIDEO_ID"
  python -m video_downloader download "https://www.tiktok.com/@user/video/ID"
  python -m video_downloader download "https://www.instagram.com/reel/ID" --quality 720p
  python -m video_downloader download "https://www.youtube.com/watch?v=ID" --audio-only
  python -m video_downloader list
  python -m video_downloader delete "video_name.mp4"
        """,
    )

    sub = parser.add_subparsers(dest="command")

    # info
    p_info = sub.add_parser("info", help="Fetch video metadata without downloading")
    p_info.add_argument("url")

    # download
    p_dl = sub.add_parser("download", help="Download a video")
    p_dl.add_argument("url")
    p_dl.add_argument(
        "--quality", "-q",
        choices=["best", "1080p", "720p", "480p", "360p", "240p", "144p"],
        default="best",
    )
    p_dl.add_argument("--audio-only", "-a", action="store_true")
    p_dl.add_argument("--output", "-o", help="Output filename without extension")

    # list / delete
    sub.add_parser("list", help="List downloaded files")
    p_del = sub.add_parser("delete", help="Delete a downloaded file")
    p_del.add_argument("filename")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(0)

    downloader = VideoDownloader(download_dir=_DOWNLOAD_DIR)

    if args.command == "info":
        get_info_command(downloader, args.url)
    elif args.command == "download":
        download_command(downloader, args.url, args.quality, args.audio_only, args.output)
    elif args.command == "list":
        list_downloads_command(downloader)
    elif args.command == "delete":
        delete_command(args.filename)


if __name__ == "__main__":
    main()
