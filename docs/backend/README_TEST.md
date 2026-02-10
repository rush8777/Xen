# Gemini Client Test Script

## Purpose
Isolated test script to verify the Gemini client functionality for video upload and analysis.

## Usage

### Method 1: Command Line
```bash
cd d:\web_dev\v0-social\backend
python test_gemini_client.py "path\to\your\video.mp4"
```

### Method 2: Place Video in Directory
1. Copy your video file to `d:\web_dev\v0-social\backend\`
2. Run: `python test_gemini_client.py`
3. Script will auto-detect the video file

## What It Tests

1. **Video Upload**: Uploads your video to Gemini cloud storage
2. **Single Interval**: Analyzes 0-5 second interval
3. **Multiple Intervals**: Analyzes multiple 5-second intervals
4. **Error Handling**: Shows detailed logging and error messages

## Expected Output

```
🧪 Gemini Client Isolated Test
==================================================
📹 Found video file: your_video.mp4
🎥 Testing video: your_video.mp4
📁 Video file size: 1234567 bytes

📤 Step 1: Uploading video to Gemini...
INFO: Processing interval 0-5s for file: files/abc123...
INFO: Calling Gemini API for interval 0-5s with mime_type: video/mp4
INFO: Gemini API response received for interval 0-5s
INFO: Response type: <class 'google.generativeai.types.GenerateContentResponse'>
INFO: Response text length: 150
✅ Video uploaded successfully! File name: files/abc123...

🔍 Step 2: Testing single interval analysis...
INFO: Successfully generated description for interval 0-5s: The video shows...
✅ Single interval analysis successful!
📝 Description: The video shows a person walking in a park...

🎬 Step 3: Testing multiple interval analysis...
📊 Generated 4 intervals: [(0, 5), (5, 10), (10, 15), (15, 20)]
✅ Multiple interval analysis successful!

📋 Analysis Results:
[00:00–00:05] The video shows a person walking in a park...
[00:05–00:10] The person continues walking and approaches a bench...
[00:10–00:15] The person sits down on the bench...
[00:15–00:20] The person looks around the park surroundings...

🎉 All tests passed!
```

## Troubleshooting

- **API Key Issues**: Make sure your GEMINI_API_KEY is set correctly
- **File Not Found**: Check the video file path
- **Upload Errors**: Check internet connection and API quota
- **Analysis Errors**: Check the backend logs for detailed error messages

## Supported Video Formats
- MP4, AVI, MOV, MKV, WebM
- Recommended: MP4 under 50MB for faster uploads
