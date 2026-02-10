# Video Downloader CLI

A simple command-line tool to download videos from YouTube, Facebook, TikTok, Instagram, and 1000+ other platforms using yt-dlp.

## Features

- 📥 Download videos from multiple platforms
- 🎵 Extract audio-only (MP3)
- 🎬 Multiple quality options (best, 1080p, 720p, 480p, 360p)
- ℹ️ Get video information without downloading
- 📁 List and manage downloaded files
- 🔧 Simple configuration via environment variables

## Installation

1. **Clone or download this repository**

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install FFmpeg (required for audio extraction and some video formats):**
   
   - **Ubuntu/Debian:**
     ```bash
     sudo apt update
     sudo apt install ffmpeg
     ```
   
   - **macOS:**
     ```bash
     brew install ffmpeg
     ```
   
   - **Windows:**
     Download from [ffmpeg.org](https://ffmpeg.org/download.html)

4. **Configure (optional):**
   ```bash
   cp .env.example .env
   # Edit .env to customize settings
   ```

## Usage

### Get Video Information

Get metadata about a video without downloading it:

```bash
python main.py info "https://www.youtube.com/watch?v=VIDEO_ID"
```

This displays:
- Title, platform, uploader
- Duration and view count
- Available formats and quality options

### Download Video

**Download in best quality:**
```bash
python main.py download "https://www.youtube.com/watch?v=VIDEO_ID"
```

**Download in specific quality:**
```bash
python main.py download "https://www.youtube.com/watch?v=VIDEO_ID" --quality 720p
```

**Download audio only (MP3):**
```bash
python main.py download "https://www.youtube.com/watch?v=VIDEO_ID" --audio-only
```

**Custom output filename:**
```bash
python main.py download "https://www.youtube.com/watch?v=VIDEO_ID" --output "my_video"
```

### List Downloaded Files

View all files in the download directory:

```bash
python main.py list
```

### Delete Downloaded File

Remove a specific file:

```bash
python main.py delete "video_name.mp4"
```

## Command Reference

```
python main.py <command> [options]

Commands:
  info        Get video information without downloading
  download    Download video
  list        List downloaded files
  delete      Delete a downloaded file

Options for 'download':
  --quality, -q     Video quality: best, 1080p, 720p, 480p, 360p (default: best)
  --audio-only, -a  Download audio only (MP3)
  --output, -o      Custom output filename (without extension)
```

## Supported Platforms

This tool supports 1000+ websites including:
- YouTube
- Facebook
- Instagram
- TikTok
- Twitter/X
- Vimeo
- Dailymotion
- Reddit
- Twitch
- LinkedIn
- And many more...

For a complete list, visit: [yt-dlp supported sites](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md)

## Configuration

Create a `.env` file to customize settings:

```env
# Download directory
DOWNLOAD_DIR=./downloads

# Maximum file size in MB
MAX_FILE_SIZE_MB=500

# File retention in hours
FILE_RETENTION_HOURS=24

# FFmpeg path (optional, auto-detect if not set)
FFMPEG_PATH=/usr/bin/ffmpeg
```

## Examples

**Get info about a YouTube video:**
```bash
python main.py info "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

**Download a TikTok video:**
```bash
python main.py download "https://www.tiktok.com/@user/video/1234567890"
```

**Download Instagram reel in 720p:**
```bash
python main.py download "https://www.instagram.com/reel/XXXXX/" --quality 720p
```

**Extract audio from YouTube video:**
```bash
python main.py download "https://www.youtube.com/watch?v=dQw4w9WgXcQ" --audio-only
```

**Download with custom name:**
```bash
python main.py download "https://www.youtube.com/watch?v=dQw4w9WgXcQ" --output "rickroll"
```

## Troubleshooting

**Error: "ffmpeg not found"**
- Install FFmpeg (see Installation section)
- Or set FFMPEG_PATH in .env file

**Error: "Download failed"**
- Check if the URL is valid
- Some platforms may require authentication
- Try updating yt-dlp: `pip install -U yt-dlp`

**Slow downloads:**
- This depends on your internet connection and the video host's servers
- Try a different quality option

## License

This project uses yt-dlp. Please respect copyright laws and the terms of service of the platforms you download from.

## Credits

Built with [yt-dlp](https://github.com/yt-dlp/yt-dlp) - A youtube-dl fork with additional features and fixes.
