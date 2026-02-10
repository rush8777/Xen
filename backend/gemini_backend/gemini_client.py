import asyncio
from pathlib import Path
from typing import List, Tuple

from google import genai
from google.genai import types

from . import config
from .video_processor import format_timestamp



# -------------------------------------------------------------------
# Gemini Client
# -------------------------------------------------------------------

client = genai.Client(api_key=config.GEMINI_API_KEY)


# -------------------------------------------------------------------
# System Instructions (STRICT)
# -------------------------------------------------------------------

SYSTEM_INSTRUCTIONS = """


ROLE

You are a computer-vision reporting system, not an analyst, narrator, or summarizer.
Your job is to produce a ground-truth visual log.

You are given one single continuous video in full.
You have access to the entire video timeline, but you must still report observations at fixed 5-second intervals.

TEMPORAL RULES (ABSOLUTE)

Observe the video at exact 5-second intervals starting from 00:00–00:05 
Continue sequentially until the video ends
DO NOT skip any interval
DO NOT merge intervals
Each interval must have its own complete description, even if nothing changes
Intervals are time-based, not clip-based

OBSERVATION-ONLY RULES (ANTI-HALLUCINATION CORE)

You MUST:

Describe only what is directly visible on screen
Use literal, surface-level language
Prefer explicit uncertainty over guessing
State visibility limits clearly

You MUST NOT:

Infer intent, emotion, purpose, or cause
Assume continuity beyond what is visible
Identify people unless identity is explicitly shown as readable on-screen text
Guess obscured or off-screen elements
Use interpretive phrases such as:

"appears to be"
"seems"
"probably"
"likely"
"suggests"

If something cannot be verified visually, state:

"Not visually identifiable."

REQUIRED OUTPUT STRUCTURE (MANDATORY)

Use the following structure for every interval:

INTERVAL: [MM:SS – MM:SS]

1. CAMERA & FRAME
2. ENVIRONMENT & BACKGROUND
3. PEOPLE / HUMAN FIGURES
4. OBJECTS & PROPS
5. TEXT & SYMBOLS
6. MOTION & CHANGES
7. LIGHTING & COLOR
8. AUDIO-VISIBLE INDICATORS
9. OCCLUSIONS & VISIBILITY LIMITS

SECTION RULES
**Should contain 200 words for each section**

1. CAMERA & FRAME

Camera position (static / moving / panning / zooming)
Framing (wide, medium, close-up)
Orientation (landscape / portrait)
On-screen overlays or UI elements

2. ENVIRONMENT & BACKGROUND

Physical setting only if visually obvious
Visible surfaces, structures, scenery
Foreground / midground / background elements

3. PEOPLE / HUMAN FIGURES

If present:

Count of individuals
Clothing, posture, visible physical traits
Observable actions only

No emotions, roles, or identity assumptions.

4. OBJECTS & PROPS

All visible objects
Shape, color, size (relative), material if visually clear
Position and motion state

5. TEXT & SYMBOLS

Transcribe text exactly as shown
Preserve case and spelling
If unreadable: state so explicitly

6. MOTION & CHANGES

Describe visible motion within the interval
If no motion: explicitly state "No visible motion"

7. LIGHTING & COLOR

Brightness level
Light sources if visible
Dominant colors and shadows

8. AUDIO-VISIBLE INDICATORS

Visual-only cues of sound (e.g., mouth movement, subtitles, microphones).
No audio inference.

9. OCCLUSIONS & VISIBILITY LIMITS

Cropped, blurred, obstructed elements
Any uncertainty or visibility limitation

FAILURE HANDLING

Blank or black frames must be described as such
Repeated scenes must still be fully described per interval
If nothing changes, still output all sections

FINAL HARD RULES

No summarization
No conclusions
No cross-interval reasoning
Skip if data is insufficient to analyze and keep a note "Cannot describe"
No compression or stylistic language
Accuracy over completeness


End output at the final interval only.
""".strip()


# -------------------------------------------------------------------
# Upload Video
# -------------------------------------------------------------------

async def upload_video_to_gemini(video_path: Path) -> str:
    """
    Upload video to Gemini and return file.name
    """
    loop = asyncio.get_running_loop()

    file = await loop.run_in_executor(
        None,
        lambda: client.files.upload(file=str(video_path))
    )

    # Wait until file is ready
    while file.state == "PROCESSING":
        await asyncio.sleep(1)
        file = client.files.get(name=file.name)

    if file.state != "ACTIVE":
        raise RuntimeError(f"File upload failed: {file.state}")

    return file.name


# -------------------------------------------------------------------
# Interval Analysis
# -------------------------------------------------------------------

async def get_interval_description(
    file_name: str,
    start: int,
    end: int,
    mime_type: str = "video/mp4"  # add mime_type parameter
) -> str:
    """
    Generate strict visual description for a time interval with robust error handling
    """
    try:
        # Validate inputs
        if not file_name:
            raise ValueError("file_name cannot be empty")
        if start < 0 or end < 0:
            raise ValueError("start and end times must be non-negative")
        if start >= end:
            raise ValueError("start time must be less than end time")
        
        # Normalize file URI
        file_uri = file_name
        if not file_uri.startswith("https://generativelanguage.googleapis.com/files/"):
            if file_uri.startswith("files/"):
                file_uri = f"https://generativelanguage.googleapis.com/{file_uri}"
            else:
                file_uri = f"https://generativelanguage.googleapis.com/files/{file_uri}"
        
        
        # Create prompt
        prompt = f"""
Observe the video ONLY from {start} seconds to {end} seconds.

RULES:
- Do NOT analyze or interpret
- Do NOT summarize across intervals
- Skip  if nothing changes and keep a note "Cannot describe"
- Describe ONLY what is visually present

Describe:
- Visible subjects
- Actions and movements
- Environment and setting
- Colors, lighting, composition
- Visible text
- Camera movement

Provide 200 words of pure visual observation.
""".strip()
        
        # Get event loop
        loop = asyncio.get_running_loop()
        
        # Define generation function
        def generate():
            try:
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=[
                        types.Content(
                            role="user",
                            parts=[
                                types.Part(
                                    file_data=types.FileData(
                                        file_uri=file_uri,
                                        mime_type=mime_type
                                    )
                                ),
                                types.Part(text=prompt)
                            ],
                        )
                    ],
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_INSTRUCTIONS,
                        temperature=0.1
                          # Increased from 300 to 800
                    )
                )
                
                return response
                
            except Exception as e:
                raise RuntimeError(f"Gemini API call failed: {str(e)}") from e
        
        # Execute with timeout
        response = await asyncio.wait_for(
            loop.run_in_executor(None, generate),
            timeout=30.0  # 30 second timeout
        )
        
        result = response.text.strip()
        
        if not result:
            raise ValueError("Empty response from Gemini API")
        
        return result
        
    except asyncio.TimeoutError:
        raise TimeoutError(f"Request timed out for interval {start}-{end}s")
    except ValueError as e:
        raise ValueError(f"Validation error: {str(e)}") from e
    except RuntimeError as e:
        raise RuntimeError(f"API error for interval {start}-{end}s: {str(e)}") from e
    except Exception as e:
        raise Exception(f"Unexpected error processing interval {start}-{end}s: {str(e)}") from e


# -------------------------------------------------------------------
# Analyze All Intervals (Concurrent + Throttled)
# -------------------------------------------------------------------

async def analyze_video_intervals(
    file_name: str,
    intervals: List[Tuple[int, int]]
) -> List[Tuple[str, str]]:
    """
    Analyze video intervals concurrently with rate limiting
    """

    semaphore = asyncio.Semaphore(config.MAX_CONCURRENT_REQUESTS)

    async def analyze_one(start: int, end: int):
        async with semaphore:
            timestamp = format_timestamp(start, end)
            try:
                description = await get_interval_description(
                    file_name, start, end
                )
                return timestamp, description
            except Exception as e:
                return timestamp, f"Error: {str(e)}"

    tasks = [
        analyze_one(start, end)
        for start, end in intervals
    ]

    return await asyncio.gather(*tasks)
