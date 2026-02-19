# Video Analysis API Scripts (Windows Batch Files)

These Windows batch files (.bat) allow you to call the backend `/analyze-from-url` endpoint directly from the command line.

## Files Created

1. **`analyze_video.bat`** - Main script to start video analysis
2. **`check_progress.bat`** - Helper script to check analysis progress
3. **`README_BAT_USAGE.md`** - This documentation file

## Prerequisites

1. **Backend server** must be running on `http://localhost:8000`
2. **curl** must be installed (usually included with Windows 10/11)
3. **PowerShell** must be available (included with Windows)

## Usage

### 1. Start Video Analysis

```cmd
REM Basic usage
analyze_video.bat "https://www.youtube.com/watch?v=VIDEO_ID"

REM With custom project name
analyze_video.bat "https://www.youtube.com/watch?v=VIDEO_ID" "My Video Project"

REM With auto-polling (continuously check progress)
analyze_video.bat "https://www.youtube.com/watch?v=VIDEO_ID" "My Project" --poll
```

### 2. Check Progress Manually

```cmd
check_progress.bat <job_id>
```

### 3. Direct API Calls

```cmd
REM Start analysis
curl -X POST -H "Content-Type: application/json" -d "{\"url\":\"https://www.youtube.com/watch?v=VIDEO_ID\",\"project_name\":\"My Project\"}\" http://localhost:8000/api/analyze-from-url

REM Check progress
curl http://localhost:8000/api/analysis/progress/<job_id>
```

## Supported Platforms

- YouTube
- TikTok
- Facebook
- Instagram
- Twitter
- LinkedIn

## Examples

### Example 1: Basic YouTube Analysis
```cmd
analyze_video.bat "https://www.youtube.com/watch?v=dQw4w9WgXcQ" "Rick Roll Analysis"
```

**Output:**
```
[INFO] Starting video analysis...
[INFO] URL: https://www.youtube.com/watch?v=dQw4w9WgXcQ
[INFO] Project Name: Rick Roll Analysis
[INFO] Backend: http://localhost:8000
[INFO] Sending request to http://localhost:8000/api/analyze-from-url...
[SUCCESS] Analysis started successfully!
[SUCCESS] Job ID: 12345678-1234-1234-1234-123456789012
[INFO] You can check progress with:
  curl http://localhost:8000/api/analysis/progress/12345678-1234-1234-1234-123456789012
[INFO] Or run: check_progress.bat 12345678-1234-1234-1234-123456789012

Done.
Press any key to continue . . .
```

### Example 2: With Auto-Polling
```cmd
analyze_video.bat "https://www.youtube.com/watch?v=dQw4w9WgXcQ" "Rick Roll" --poll
```

**Output:**
```
[INFO] Starting video analysis...
[INFO] URL: https://www.youtube.com/watch?v=dQw4w9WgXcQ
[INFO] Project Name: Rick Roll
[INFO] Backend: http://localhost:8000
[INFO] Sending request to http://localhost:8000/api/analyze-from-url...
[SUCCESS] Analysis started successfully!
[SUCCESS] Job ID: 12345678-1234-1234-1234-123456789012
[INFO] Auto-polling for progress...
Step 0: Initializing video analysis (Status: running)
Step 1: Downloading video (Status: running)
Step 2: Extracting comments (Status: running)
Step 3: Running Gemini analysis (Status: running)
Step 4: Creating project (Status: running)
Step 5: Opening Streamline (Status: completed)
[SUCCESS] Analysis completed!
[SUCCESS] Project ID: 123

Done.
Press any key to continue . . .
```

### Example 3: Check Progress Manually
```cmd
check_progress.bat "12345678-1234-1234-1234-123456789012"
```

**Output:**
```
[INFO] Checking progress for job: 12345678-1234-1234-1234-123456789012
Job ID: 12345678-1234-1234-1234-123456789012
Status: running
Step: 3
Text: Running Gemini analysis
[INFO] Analysis in progress...

Press any key to continue . . .
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
```cmd
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### curl Not Found
```
'curl' is not recognized as an internal or external command...
```
**Solution**: Install curl or use Windows built-in curl (Windows 10/11 includes it)

### PowerShell Execution Policy
If you get PowerShell execution policy errors, run:
```cmd
powershell -Command "Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser"
```

### Invalid URL
```
[ERROR] Failed to start analysis (HTTP 422)
```
**Solution**: Ensure the URL includes the protocol (http:// or https://) and is properly quoted

### Video Not Found
```
[ERROR] Failed to start analysis (HTTP 500)
Response: {"detail":"Video not found or download failed"}
```
**Solution**: Verify the video URL is correct and accessible

## Quick Test

To test if everything is working:

1. **Start the backend:**
   ```cmd
   cd backend
   python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **In a new terminal, test the analysis:**
   ```cmd
   analyze_video.bat "https://www.youtube.com/watch?v=dQw4w9WgXcQ" "Test Video"
   ```

3. **Check progress:**
   ```cmd
   check_progress.bat <job_id_from_previous_step>
   ```

## Notes

- The batch files create temporary files in `%TEMP%` and clean them up automatically
- Auto-polling checks progress every 2 seconds
- All scripts pause at the end so you can read the output
- URLs with special characters should be enclosed in quotes
