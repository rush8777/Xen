import cv2
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from typing import List, Tuple
from . import config


def get_video_duration(video_path: Path) -> float:
    """Get video duration in seconds using OpenCV"""
    video = cv2.VideoCapture(str(video_path))
    fps = video.get(cv2.CAP_PROP_FPS)
    frame_count = video.get(cv2.CAP_PROP_FRAME_COUNT)
    video.release()
    
    if fps > 0:
        duration = frame_count / fps
        return duration
    return 0.0


def generate_timestamps(duration: float) -> List[Tuple[int, int]]:
    """Generate 5-second interval timestamps"""
    intervals = []
    interval_size = config.INTERVAL_SECONDS
    
    current = 0
    while current < duration:
        end = min(current + interval_size, int(duration) + 1)
        intervals.append((current, end))
        current = end
    
    return intervals


def format_timestamp(start: int, end: int) -> str:
    """Format timestamp as [MM:SS–MM:SS] with en-dash"""
    def seconds_to_mmss(seconds: int) -> str:
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes:02d}:{secs:02d}"
    
    return f"[{seconds_to_mmss(start)}–{seconds_to_mmss(end)}]"


def _sanitize_filename_part(value: str) -> str:
    value = (value or "").strip()
    if not value:
        return "unknown"
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value or "unknown"


def _video_link_slug(video_url: str) -> str:
    raw = (video_url or "").strip()
    if not raw:
        return "unknown"

    try:
        parsed = urlparse(raw)
        host = (parsed.hostname or "").replace("www.", "")

        qs = parse_qs(parsed.query)
        v = qs.get("v", [None])[0]
        if v:
            return _sanitize_filename_part(f"{host}_{v}")

        path = (parsed.path or "").strip("/")
        if path:
            tail = path.split("/")[-1]
            return _sanitize_filename_part(f"{host}_{tail}")

        return _sanitize_filename_part(host) if host else "unknown"
    except Exception:
        return _sanitize_filename_part(raw)


def build_results_filename(
    *,
    platform: str | None,
    video_url: str | None,
    model: str | None,
    platform_published_date: str | None,
    ext: str = ".txt",
    max_len: int = 180,
) -> str:
    platform_part = _sanitize_filename_part(platform or "")
    link_part = _video_link_slug(video_url or "")
    model_part = _sanitize_filename_part((model or "").replace("models/", ""))

    date_raw = (platform_published_date or "").strip()
    if date_raw:
        date_part = _sanitize_filename_part(date_raw)
    else:
        date_part = datetime.utcnow().strftime("%Y%m%d")

    filename = f"{platform_part}_{link_part}_{model_part}_{date_part}{ext}"
    if len(filename) > max_len:
        base, extension = filename[: -len(ext)], ext
        filename = base[: max_len - len(extension)] + extension
    return filename


async def save_descriptions(
    job_id: str,
    descriptions: List[Tuple[str, str]],
    *,
    output_filename: str | None = None,
):
    """Save descriptions to output file"""

    if output_filename:
        output_path = config.OUTPUT_DIR / output_filename
    else:
        output_path = config.OUTPUT_DIR / f"{job_id}_results.txt"

    if output_path.exists():
        stem = output_path.stem
        suffix = output_path.suffix
        output_path = output_path.with_name(f"{stem}_{job_id[:8]}{suffix}")

    with open(output_path, "w", encoding="utf-8") as f:
        for timestamp, description in descriptions:
            f.write(f"{timestamp}\n")
            f.write(f"{description}\n\n")

    return output_path
