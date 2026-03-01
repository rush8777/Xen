"""
Comments extractor placeholder for the Cobalt-only backend.

Cobalt is used for media download. Comment extraction is currently disabled
in this runtime and returns an empty result shape.
"""

from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
import json
from typing import Dict, Generator, List, Optional


@dataclass
class Comment:
    id: str
    text: str
    author: str
    author_id: Optional[str]
    like_count: int
    reply_count: int
    timestamp: Optional[str]
    is_reply: bool = False
    parent_id: Optional[str] = None


class CommentsExtractor:
    """
    Cobalt-only placeholder.
    """

    def __init__(self, output_dir: str = "./extracted_comments"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    @staticmethod
    def is_available() -> bool:
        return False

    def extract_comments(
        self,
        url: str,
        max_comments: Optional[int] = None,
        include_replies: bool = True,
    ) -> Dict:
        _ = max_comments, include_replies
        return {
            "video_info": {
                "title": "Unknown",
                "id": "Unknown",
                "uploader": "Unknown",
                "platform": "Unknown",
                "comment_count": 0,
                "url": url,
                "extracted_at": datetime.now().isoformat(),
            },
            "comments_count": 0,
            "comments": [],
        }

    def _parse_comment(self, data: Dict) -> Comment:
        return Comment(
            id=str(data.get("id", "")),
            text=data.get("text", ""),
            author=data.get("author", "Unknown"),
            author_id=data.get("author_id"),
            like_count=data.get("like_count", 0) or 0,
            reply_count=len(data.get("replies", []))
            if isinstance(data.get("replies"), list)
            else 0,
            timestamp=data.get("timestamp"),
            is_reply=data.get("parent") is not None,
            parent_id=str(data.get("parent")) if data.get("parent") else None,
        )

    def extract_and_save(
        self,
        url: str,
        output_filename: Optional[str] = None,
        max_comments: Optional[int] = None,
        include_replies: bool = True,
        format: str = "json",
    ) -> str:
        result = self.extract_comments(url, max_comments, include_replies)
        if not output_filename:
            output_filename = "comments_unavailable"
        output_path = self.output_dir / f"{output_filename}.{format}"
        if format == "json":
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
        elif format == "txt":
            with open(output_path, "w", encoding="utf-8") as f:
                f.write("Comments extraction is currently disabled in this runtime.\n")
                f.write(f"URL: {url}\n")
        else:
            raise ValueError(f"Unsupported format: {format}")
        return str(output_path)

    def stream_comments(
        self,
        url: str,
        max_comments: Optional[int] = None,
    ) -> Generator[Comment, None, None]:
        _ = url, max_comments
        if False:
            yield Comment(
                id="",
                text="",
                author="",
                author_id=None,
                like_count=0,
                reply_count=0,
                timestamp=None,
            )


def extract_comments_cli():
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description="Comments extraction is disabled in this Cobalt-only build."
    )
    parser.add_argument("url", help="Video URL")
    args = parser.parse_args()

    extractor = CommentsExtractor()
    output_path = extractor.extract_and_save(url=args.url, format="json")
    print(f"Comments extraction unavailable. Wrote placeholder: {output_path}")
    sys.exit(0)


if __name__ == "__main__":
    extract_comments_cli()
