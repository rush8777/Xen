import cv2
from pathlib import Path
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


async def save_descriptions(job_id: str, descriptions: List[Tuple[str, str]]):
    """Save descriptions to output file"""
    output_path = config.OUTPUT_DIR / f"{job_id}_results.txt"
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for timestamp, description in descriptions:
            f.write(f"{timestamp}\n")
            f.write(f"{description}\n\n")
    
    return output_path
