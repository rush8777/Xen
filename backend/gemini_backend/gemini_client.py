import asyncio
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

from google import genai
from google.genai import types

from . import config
 



# -------------------------------------------------------------------
# Gemini Client
# -------------------------------------------------------------------

client = genai.Client(api_key=config.GEMINI_API_KEY)


# -------------------------------------------------------------------
# Cached-content system instruction (NEUTRAL)
# -------------------------------------------------------------------

# NOTE:
# Cached content "system_instruction" becomes the default global framing for all
# subsequent `generate_content` calls that reference `cached_content_name`.
# We keep this neutral so the caller prompts (overview/stats/etc.) fully control
# output format. This intentionally removes any interval/20-second analysis rules.
CACHED_VIDEO_SYSTEM_INSTRUCTION = """
You are a multimodal assistant that can analyze the provided video.
Follow the user's prompt precisely.
If something cannot be verified from the video, say so explicitly.
Return outputs in the format requested by the prompt.
""".strip()


# -------------------------------------------------------------------
# Upload Video
# -------------------------------------------------------------------

async def upload_video_to_gemini(video_path: Path) -> str:
    """
    Upload video to Gemini and create cached content, return cached content name.

    The cached content is created with a neutral system instruction so other
    downstream calls (overview generation, etc.) can fully control behavior.
    """
    loop = asyncio.get_running_loop()

    # Step 1: Upload the video file
    file = await loop.run_in_executor(
        None,
        lambda: client.files.upload(file=str(video_path))
    )

    # Wait until file is ready
    while getattr(file.state, "name", None) == "PROCESSING":
        await asyncio.sleep(1)
        file = client.files.get(name=file.name)

    if getattr(file.state, "name", None) != "ACTIVE":
        raise RuntimeError(f"File upload failed: {getattr(file.state, 'name', file.state)}")

    # Step 2: Create cached content from the uploaded file
    cache = await loop.run_in_executor(
        None,
        lambda: client.caches.create(
            model="models/gemini-2.5-flash",
            config=types.CreateCachedContentConfig(
                display_name=f"video-analysis-{video_path.stem[:12]}",
                system_instruction=CACHED_VIDEO_SYSTEM_INSTRUCTION,
                contents=[file],
                ttl="3600s",  # 1 hour cache
            ),
        )
    )

    return cache.name


# -------------------------------------------------------------------
# Cached Video Analysis Functions (Statistics, Overview, SWOT)
# -------------------------------------------------------------------

async def call_gemini_with_cached_video(
    *,
    cached_content_name: str,
    prompt: str,
    model: str = "models/gemini-2.5-flash",
    response_mime_type: str = "application/json",
) -> str:
    """
    Shared low-level helper to call Gemini using existing cached video content.

    This keeps requests cheap by:
    - Reusing the uploaded video via cached_content_name
    - Sending only a compact text prompt per call
    """
    if not cached_content_name:
        raise ValueError("cached_content_name is required")

    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
            cached_content=cached_content_name,
            temperature=1.0,
            response_mime_type=response_mime_type,
        ),
    )

    text = (response.text or "").strip()
    if not text:
        raise ValueError("Empty response from Gemini (cached video call)")
    return text


async def generate_statistics_from_cached_video(
    *,
    cached_content_name: str,
    duration_seconds: float,
    video_url: str,
    project_name: str,
) -> Dict[str, Any]:
    """
    Generate all statistics components from cached video using component-by-component approach.
    Uses the legacy statistics_prompts system but with cached video content instead of text files.

    Returns a dict shaped like the raw output expected by ProjectStatisticsGenerator:
      {
        "video_metrics_grid": {...},
        "sentiment_pulse": [...],
        "emotion_radar": [...],
        "emotional_intensity_timeline": [...],
        "audience_demographics.age_distribution": [...],
        "audience_demographics.gender_distribution": [...],
        "audience_demographics.top_locations": [...],
        "audience_demographics.audience_interests": [...],
        "top_comments": [...]
      }
    """
    # Import here to avoid circular dependencies
    try:
        from .statistics_prompts import statistics_prompts
    except ImportError:
        from statistics_prompts import statistics_prompts

    # Component names matching the legacy approach
    COMPONENT_NAMES = [
        "video_metrics_grid",
        "sentiment_pulse",
        "emotion_radar",
        "emotional_intensity_timeline",
        "audience_demographics.age_distribution",
        "audience_demographics.gender_distribution",
        "audience_demographics.top_locations",
        "audience_demographics.audience_interests",
        "top_comments",
    ]

    results = {}

    # Generate each component individually using cached video
    for component_name in COMPONENT_NAMES:
        try:
            # Build prompt using existing statistics_prompts system
            # Pass empty compact_data since we're using cached video directly
            prompt = statistics_prompts.build_prompt(
                component_name=component_name,
                compact_data="",  # Empty - using cached video instead of text
                video_url=video_url,
                project_name=project_name,
            )

            # Call Gemini with cached video content
            text = await call_gemini_with_cached_video(
                cached_content_name=cached_content_name,
                prompt=prompt,
            )

            # Parse JSON response
            try:
                component_data = json.loads(text)
                results[component_name] = component_data
            except json.JSONDecodeError as e:
                # On error, use empty/default structure for this component
                print(f"  ❌ {component_name}: Invalid JSON - {str(e)}")
                # Return appropriate default based on component type
                if component_name == "video_metrics_grid":
                    results[component_name] = {
                        "net_sentiment_score": 50,
                        "net_sentiment_delta_vs_last": 0,
                        "engagement_velocity_comments_per_hour": 0,
                        "toxicity_alert_bots_detected": 0,
                        "question_density_percent": 0,
                    }
                else:
                    results[component_name] = []

        except Exception as e:
            print(f"  ❌ {component_name}: {str(e)}")
            # Return appropriate default based on component type
            if component_name == "video_metrics_grid":
                results[component_name] = {
                    "net_sentiment_score": 50,
                    "net_sentiment_delta_vs_last": 0,
                    "engagement_velocity_comments_per_hour": 0,
                    "toxicity_alert_bots_detected": 0,
                    "question_density_percent": 0,
                }
            else:
                results[component_name] = []

    return results


#
# NOTE: Interval-based SWOT generation was intentionally removed.
# This module now focuses on cached-video upload + cached calls for overview/statistics.