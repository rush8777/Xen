# Video Analyzer CLI

A command-line tool to analyze videos using Google Gemini AI. Analyzes videos in 5-second intervals and provides objective visual descriptions.

## Features

- 🎬 Analyze videos with AI-powered descriptions
- ⚡ Concurrent interval processing for speed
- 💾 Intelligent caching to avoid re-uploading same videos
- 📊 5-second interval-based analysis
- 🔄 Automatic cache expiry management
- 📝 Text output with timestamped descriptions

## Installation

### 1. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 2. Get Google Gemini API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create an API key
3. Set it as an environment variable:

```bash
export GEMINI_API_KEY='your-api-key-here'
```

Or create a `.env` file:
```bash
cp .env.example .env
# Edit .env and add your API key
```

### 3. Verify installation

```bash
python main.py info
```

## Usage

### Analyze a Video

```bash
python main.py analyze video.mp4
```

This will:
1. Check if video is in cache (SHA256 hash)
2. Upload to Gemini if not cached
3. Analyze in 5-second intervals
4. Generate timestamped descriptions
5. Save results to `outputs/` directory

**With custom output:**
```bash
python main.py analyze video.mp4 --output my_results.txt
```

### Manage Cache

**List cached videos:**
```bash
python main.py cache-list
```

**Clean up expired cache entries:**
```bash
python main.py cache-cleanup
```

### System Information

```bash
python main.py info
```

Shows:
- Directory paths
- Configuration settings
- API key status

## Command Reference

```
python main.py <command> [options]

Commands:
  analyze         Analyze a video file
  cache-list      List all cached videos
  cache-cleanup   Remove expired cache entries
  info           Show system information

Options for 'analyze':
  --output, -o    Custom output file path
```

## How It Works

### 1. Video Upload
- Calculates SHA256 hash of video
- Checks cache for existing Gemini reference
- If cached: uses existing reference (saves time & API calls)
- If not: uploads to Gemini API

### 2. Interval Analysis
- Divides video into 5-second intervals
- Analyzes each interval concurrently (up to 10 at a time)
- Generates objective visual descriptions
- No interpretation, just pure observation

### 3. Output Format
```
[00:00–00:05]
A person wearing a blue shirt stands in front of a white wall. 
The lighting is bright and even. Camera is stationary.

[00:05–00:10]
The same person gestures with their hands while speaking. 
Background remains unchanged. Slight camera movement detected.
```

## Configuration

Edit `config.py` or set environment variables:

```python
# Processing settings
INTERVAL_SECONDS = 5              # Interval duration
MAX_CONCURRENT_REQUESTS = 10      # Concurrent API calls

# Cache settings
CACHE_EXPIRY_HOURS = 1           # Cache lifetime
```

## Project Structure

```
gemini-cli/
├── main.py                # CLI interface
├── gemini_client.py       # Gemini API client
├── video_processor.py     # Video processing utilities
├── cache_manager.py       # Cache management
├── config.py             # Configuration
├── requirements.txt      # Dependencies
├── .env.example         # Environment template
│
├── uploads/             # Temporary video storage
├── outputs/             # Analysis results
└── cache/              # Cache database
    └── video_cache.json
```

## Examples

### Basic Analysis

```bash
# Analyze a YouTube video (after downloading)
python main.py analyze downloaded_video.mp4

# Output saved to: outputs/{job_id}_results.txt
```

### With Custom Output

```bash
# Save to specific location
python main.py analyze video.mp4 --output ~/Documents/analysis.txt
```

### Cache Management

```bash
# Check what's cached
python main.py cache-list

# Output:
# 1. Hash: 5a9b2c3d4e5f6a7b...
#    Filename: video.mp4
#    Duration: 120.50s
#    Status: ✅ Active (0.8h remaining)
```

## Advanced Usage

### Batch Processing

Create a bash script to process multiple videos:

```bash
#!/bin/bash
# batch_analyze.sh

for video in videos/*.mp4; do
    echo "Analyzing: $video"
    python main.py analyze "$video"
done
```

### Integration with Other Tools

```python
import asyncio
from pathlib import Path
from main import VideoAnalyzer

async def analyze_programmatically():
    analyzer = VideoAnalyzer()
    
    # Create job
    job_id = analyzer.create_job(Path("video.mp4"))
    
    # Analyze
    output_path = await analyzer.analyze_job(job_id)
    
    # Read results
    with open(output_path) as f:
        results = f.read()
    
    return results

# Run
results = asyncio.run(analyze_programmatically())
print(results)
```

## Cache System

### How Caching Works

1. **Hash Calculation**: SHA256 hash of entire video file
2. **Cache Lookup**: Check if hash exists in `cache/video_cache.json`
3. **Cache Hit**: Use existing Gemini URI (no upload needed)
4. **Cache Miss**: Upload to Gemini, save URI to cache
5. **Expiry**: Cache entries expire after 1 hour

### Cache Benefits

- ✅ Saves time (no re-upload)
- ✅ Saves API calls (quota-friendly)
- ✅ Faster analysis for repeated videos
- ✅ Automatic cleanup of old entries

### Cache File Format

```json
{
  "5a9b2c3d4e5f6a7b...": {
    "gemini_file_uri": "https://generativelanguage.googleapis.com/...",
    "uploaded_at": "2024-02-06T10:30:00",
    "duration": 120.5,
    "expires_at": "2024-02-06T11:30:00",
    "original_filename": "video.mp4"
  }
}
```

## Supported Video Formats

- MP4 (`.mp4`)
- AVI (`.avi`)
- MOV (`.mov`)
- MKV (`.mkv`)
- WebM (`.webm`)

## Troubleshooting

### Error: "GEMINI_API_KEY not set"

```bash
# Set environment variable
export GEMINI_API_KEY='your-api-key'

# Or create .env file
echo "GEMINI_API_KEY=your-api-key" > .env
```

### Error: "cv2 module not found"

```bash
# Install OpenCV
pip install opencv-python
```

### Error: "Video file not found"

- Check file path is correct
- Use absolute path if relative doesn't work
- Verify file exists: `ls -lh video.mp4`

### Slow Analysis

- Normal for long videos (5s per interval processing)
- Concurrent processing helps (10 intervals at once)
- Check internet connection speed
- Cache helps for repeated videos

### Cache Not Working

```bash
# Check cache status
python main.py cache-list

# Clean up and retry
python main.py cache-cleanup
```

## API Rate Limits

Google Gemini API has rate limits:
- Check your quota in Google AI Studio
- Default: 10 concurrent requests (configurable in config.py)
- Cache helps reduce API calls

## Output Examples

### Short Video (30 seconds)

```
[00:00–00:05]
A woman in a red dress stands on a wooden stage. Bright stage lights 
illuminate from above. The camera slowly zooms in from a wide shot.

[00:05–00:10]
The woman begins speaking, gesturing with her hands. The background 
shows a blue curtain. Camera remains steady at medium close-up.

[00:10–00:15]
She walks to stage left while continuing to speak. Stage lights shift 
to follow her movement. Wide shot from fixed camera position.
...
```

## Performance

- **Small video (30s)**: ~30-60 seconds analysis time
- **Medium video (5min)**: ~3-5 minutes analysis time
- **Large video (30min)**: ~15-20 minutes analysis time

Cache hits reduce this to <10 seconds for re-analyzed videos.

## Privacy & Security

- Videos are uploaded to Google Gemini API
- Cache stores file hashes and Gemini URIs
- No video content stored locally after analysis
- Follow Google's terms of service for Gemini API

## License

This tool uses Google Gemini API. Ensure you comply with Google's terms of service.

## Credits

Built with:
- [Google Gemini AI](https://ai.google.dev/)
- [OpenCV](https://opencv.org/)
- Python 3.8+
