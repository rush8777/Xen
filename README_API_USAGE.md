# Video Analysis API Scripts

These bash scripts allow you to call the backend `/analyze-from-url` endpoint directly from the command line.

## Files Created

1. **`analyze_video.sh`** - Main script to start video analysis
2. **`check_progress.sh`** - Helper script to check analysis progress
3. **`README_API_USAGE.md`** - This documentation file

## Usage

### 1. Start Video Analysis

```bash
# Basic usage
./analyze_video.sh "https://www.youtube.com/watch?v=VIDEO_ID"

# With custom project name
./analyze_video.sh "https://www.youtube.com/watch?v=VIDEO_ID" "My Video Project"

# With auto-polling (continuously check progress)
./analyze_video.sh "https://www.youtube.com/watch?v=VIDEO_ID" "My Project" --poll
```

### 2. Check Progress Manually

```bash
./check_progress.sh <job_id>
```

### 3. Direct API Calls

```bash
# Start analysis
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"url":"https://www.youtube.com/watch?v=VIDEO_ID","project_name":"My Project"}' \
  http://localhost:8000/api/analyze-from-url

# Check progress
curl http://localhost:8000/api/analysis/progress/<job_id>
```

## Supported Platforms

- YouTube
- TikTok
- Facebook
- Instagram
- Twitter
- LinkedIn

## Prerequisites

1. Backend server must be running on `http://localhost:8000`
2. On Windows: Use Git Bash, WSL, or PowerShell with appropriate modifications
3. On Unix/Linux/macOS: Scripts should work directly

## Windows Usage

Since you're on Windows, use one of these methods:

### Git Bash (Recommended)
```bash
# Navigate to project directory
cd d:/web_dev/v0-social

# Make scripts executable (Git Bash supports chmod)
chmod +x analyze_video.sh check_progress.sh

# Run scripts
./analyze_video.sh "https://www.youtube.com/watch?v=dQw4w9WgXcQ" "Test Video"
```

### PowerShell
```powershell
# Navigate to project directory
cd d:\web_dev\v0-social

# Run with bash (if available)
bash analyze_video.sh "https://www.youtube.com/watch?v=dQw4w9WgXcQ" "Test Video"
```

### WSL (Windows Subsystem for Linux)
```bash
# Navigate to project directory
cd /mnt/d/web_dev/v0-social

# Make executable and run
chmod +x analyze_video.sh check_progress.sh
./analyze_video.sh "https://www.youtube.com/watch?v=dQw4w9WgXcQ" "Test Video"
```

## Example Output

```
[INFO] Starting video analysis...
[INFO] URL: https://www.youtube.com/watch?v=dQw4w9WgXcQ
[INFO] Project Name: Test Video
[INFO] Backend: http://localhost:8000
[INFO] Sending request to http://localhost:8000/api/analyze-from-url...
[SUCCESS] Analysis started successfully!
[SUCCESS] Job ID: 12345678-1234-1234-1234-123456789012
[INFO] You can check progress with:
  curl http://localhost:8000/api/analysis/progress/12345678-1234-1234-1234-123456789012
[INFO] Or run: ./check_progress.sh 12345678-1234-1234-1234-123456789012
```

## API Response Format

### Start Analysis Response
```json
{
  "job_id": "uuid-string",
  "original_url": "https://video-url.com",
  "project_id": null
}
```

### Progress Response
```json
{
  "job_id": "uuid-string",
  "status": "running|completed|failed",
  "step": 2,
  "text": "Extracting comments",
  "project_id": 123,
  "error": null
}
```

## Analysis Steps

1. **Step 0**: Initializing video analysis
2. **Step 1**: Downloading video
3. **Step 2**: Extracting comments
4. **Step 3**: Running Gemini analysis
5. **Step 4**: Creating project
6. **Step 5**: Opening Streamline (completed)

## Troubleshooting

### Backend Not Running
```
[ERROR] Failed to start analysis (HTTP 000)
Response: 
```
**Solution**: Start the backend server:
```bash
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Invalid URL
```
[ERROR] Failed to start analysis (HTTP 422)
Response: {"detail":[{"type":"url_parsing","loc":["body","url"],"msg":"invalid or missing URL scheme","input":"invalid-url","ctx":{"error":"invalid or missing URL scheme"}}]}
```
**Solution**: Ensure the URL includes the protocol (http:// or https://)

### Video Not Found
``[ERROR] Failed to start analysis (HTTP 500)
Response: {"detail":"Video not found or download failed"}
```
**Solution**: Verify the video URL is correct and accessible
