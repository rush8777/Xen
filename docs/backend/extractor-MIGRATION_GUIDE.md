# Migration from FastAPI to CLI Application

## Overview

Your video downloader application has been successfully converted from a FastAPI web service to a standalone command-line interface (CLI) application.

## What Changed

### Removed Components
✅ **FastAPI endpoints** - No more `/download`, `/info`, `/health` endpoints  
✅ **Uvicorn server** - No web server needed  
✅ **Pydantic models** - Replaced with simple argument parsing  
✅ **HTTP requests/responses** - Direct function calls instead  
✅ **Dependencies**: fastapi, uvicorn, pydantic, pydantic-settings, python-multipart, aiofiles  

### New Components
✨ **CLI interface** - Uses Python's `argparse` for command-line arguments  
✨ **Direct execution** - Run commands directly from terminal  
✨ **Simplified config** - Environment variables without Pydantic  
✨ **Progress indicators** - Visual download progress in terminal  

## File Structure Comparison

### Before (FastAPI)
```
yt-dlp/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI app with endpoints
│   ├── config.py        # Pydantic settings
│   ├── downloader.py    # Video downloader class
│   └── utils.py
├── requirements.txt     # Heavy dependencies
└── docker-compose.yml   # Docker setup
```

### After (CLI)
```
yt-dlp-cli/
├── main.py             # CLI interface with argparse
├── config.py           # Simple settings class
├── downloader.py       # Video downloader class (mostly unchanged)
├── requirements.txt    # Minimal dependencies
├── .env.example
├── .gitignore
├── README.md
└── downloads/          # Download directory
```

## Migration Steps

### 1. Install Dependencies
```bash
cd yt-dlp-cli
pip install -r requirements.txt
```

Only 2 dependencies now:
- `yt-dlp` - Video downloader
- `python-dotenv` - Environment variables

### 2. Configuration
Create `.env` file (optional):
```bash
cp .env.example .env
```

### 3. Usage Examples

#### Before (FastAPI - HTTP requests)
```bash
# Start server
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Get info (curl)
curl -X POST "http://localhost:8000/info" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://youtube.com/watch?v=VIDEO_ID"}'

# Download (curl)
curl -X POST "http://localhost:8000/download" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://youtube.com/watch?v=VIDEO_ID", "quality": "720p"}' \
  --output video.mp4
```

#### After (CLI - Direct commands)
```bash
# Get info
python main.py info "https://youtube.com/watch?v=VIDEO_ID"

# Download
python main.py download "https://youtube.com/watch?v=VIDEO_ID" --quality 720p

# Audio only
python main.py download "https://youtube.com/watch?v=VIDEO_ID" --audio-only

# List files
python main.py list

# Delete file
python main.py delete "video_name.mp4"
```

## Feature Mapping

| FastAPI Endpoint | CLI Command | Notes |
|-----------------|-------------|-------|
| `GET /` | N/A | Service info removed |
| `GET /health` | N/A | Not needed for CLI |
| `POST /info` | `python main.py info <url>` | Same functionality |
| `POST /download` | `python main.py download <url> [options]` | Same functionality |
| `GET /downloads` | `python main.py list` | Lists downloaded files |
| `DELETE /downloads/{filename}` | `python main.py delete <filename>` | Deletes specific file |

## Benefits of CLI Version

### Advantages
✅ **Simpler** - No web server, no HTTP layer  
✅ **Lighter** - 2 dependencies vs 8  
✅ **Faster startup** - No server initialization  
✅ **Direct use** - No need for HTTP client  
✅ **Better for scripting** - Easy to integrate in bash scripts  
✅ **No port conflicts** - No need to manage ports  

### When to Use Each

**Use CLI version when:**
- Running on local machine
- Automating downloads with scripts
- One-off downloads
- Learning/testing

**Use FastAPI version when:**
- Need remote access
- Building web interface
- Multiple users
- Integration with web apps

## Testing the CLI

### Quick Test
```bash
# 1. Get video info
python main.py info "https://www.youtube.com/watch?v=jNQXAC9IVRw"

# 2. Download a short video
python main.py download "https://www.youtube.com/watch?v=jNQXAC9IVRw" --quality 360p

# 3. List downloads
python main.py list
```

### All Commands
```bash
# Help
python main.py --help
python main.py download --help

# Info
python main.py info "VIDEO_URL"

# Download variations
python main.py download "VIDEO_URL"
python main.py download "VIDEO_URL" --quality 720p
python main.py download "VIDEO_URL" --audio-only
python main.py download "VIDEO_URL" --output "custom_name"

# Management
python main.py list
python main.py delete "filename.mp4"
```

## Script Integration Example

You can now easily use this in bash scripts:

```bash
#!/bin/bash
# Download multiple videos

urls=(
    "https://youtube.com/watch?v=VIDEO1"
    "https://youtube.com/watch?v=VIDEO2"
    "https://youtube.com/watch?v=VIDEO3"
)

for url in "${urls[@]}"; do
    echo "Downloading: $url"
    python main.py download "$url" --quality 720p
done

echo "All downloads complete!"
python main.py list
```

## Troubleshooting

### Import Errors
If you get import errors, make sure you're in the `yt-dlp-cli` directory:
```bash
cd yt-dlp-cli
python main.py --help
```

### FFmpeg Not Found
Install FFmpeg for audio extraction and some video formats:
```bash
# Ubuntu/Debian
sudo apt install ffmpeg

# macOS
brew install ffmpeg
```

### Permission Denied
Make main.py executable:
```bash
chmod +x main.py
./main.py --help
```

## Next Steps

1. **Test the CLI** - Try downloading a few videos
2. **Customize** - Edit `.env` to change download directory
3. **Create alias** (optional):
   ```bash
   # Add to ~/.bashrc or ~/.zshrc
   alias yt-download='python /path/to/yt-dlp-cli/main.py'
   
   # Then use:
   yt-download download "VIDEO_URL"
   ```
4. **Add to PATH** (optional):
   ```bash
   # Make it globally accessible
   sudo ln -s /path/to/yt-dlp-cli/main.py /usr/local/bin/yt-download
   
   # Then use from anywhere:
   yt-download --help
   ```

## Summary

Your video downloader is now a simple, focused CLI tool that does one thing well: download videos. No web server overhead, no complex dependencies, just straightforward command-line usage.

Enjoy your streamlined video downloader! 🚀
