"""
Comments extractor module for extracting video comments
Supports YouTube and other platforms via yt-dlp
"""

import yt_dlp
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Generator
from ..config import settings
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class Comment:
    """Represents a single comment"""
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
    Video comments extractor using yt-dlp
    Supports YouTube and other platforms that expose comments
    """
    
    def __init__(self, output_dir: str = "./extracted_comments"):
        """
        Initialize the comments extractor
        
        Args:
            output_dir: Directory to save extracted comments
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
    def extract_comments(
        self, 
        url: str, 
        max_comments: Optional[int] = None,
        include_replies: bool = True
    ) -> Dict:
        """
        Extract all comments from a video
        
        Args:
            url: Video URL
            max_comments: Maximum number of comments to extract (None for all)
            include_replies: Whether to include reply comments
            
        Returns:
            Dictionary containing video info and comments list
        """
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'writeinfojson': False,
            'getcomments': True,  # Enable comment extraction
            'max_comments': max_comments,
            'max_comment_count': max_comments if max_comments else 0,
            'socket_timeout': settings.DOWNLOAD_TIMEOUT_SECONDS,  # 5 minutes
        }
        
        comments_list: List[Comment] = []
        video_info = {}
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # Extract video metadata
            video_info = {
                'title': info.get('title', 'Unknown'),
                'id': info.get('id', 'Unknown'),
                'uploader': info.get('uploader', 'Unknown'),
                'platform': info.get('extractor', 'Unknown'),
                'comment_count': info.get('comment_count', 0),
                'url': url,
                'extracted_at': datetime.now().isoformat(),
            }
            
            # Extract comments
            raw_comments = info.get('comments', [])
            
            for comment_data in raw_comments:
                comment = self._parse_comment(comment_data)
                
                # Skip replies if not requested
                if not include_replies and comment.is_reply:
                    continue
                    
                comments_list.append(comment)
        
        return {
            'video_info': video_info,
            'comments_count': len(comments_list),
            'comments': [asdict(c) for c in comments_list]
        }
    
    def _parse_comment(self, data: Dict) -> Comment:
        """Parse raw comment data into Comment dataclass"""
        return Comment(
            id=str(data.get('id', '')),
            text=data.get('text', ''),
            author=data.get('author', 'Unknown'),
            author_id=data.get('author_id'),
            like_count=data.get('like_count', 0) or 0,
            reply_count=len(data.get('replies', [])) if isinstance(data.get('replies'), list) else 0,
            timestamp=data.get('timestamp'),
            is_reply=data.get('parent') is not None,
            parent_id=str(data.get('parent')) if data.get('parent') else None
        )
    
    def extract_and_save(
        self, 
        url: str, 
        output_filename: Optional[str] = None,
        max_comments: Optional[int] = None,
        include_replies: bool = True,
        format: str = 'json'
    ) -> str:
        """
        Extract comments and save to file
        
        Args:
            url: Video URL
            output_filename: Custom output filename (without extension)
            max_comments: Maximum number of comments to extract
            include_replies: Whether to include reply comments
            format: Output format ('json' or 'txt')
            
        Returns:
            Path to saved file
        """
        result = self.extract_comments(url, max_comments, include_replies)
        
        # Generate filename if not provided
        if not output_filename:
            video_id = result['video_info']['id']
            platform = result['video_info']['platform']
            output_filename = f"{platform}_{video_id}_comments"
        
        output_path = self.output_dir / f"{output_filename}.{format}"
        
        if format == 'json':
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
        elif format == 'txt':
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(f"Video: {result['video_info']['title']}\n")
                f.write(f"Platform: {result['video_info']['platform']}\n")
                f.write(f"URL: {url}\n")
                f.write(f"Total Comments: {result['comments_count']}\n")
                f.write("=" * 80 + "\n\n")
                
                for comment in result['comments']:
                    f.write(f"Author: {comment['author']}\n")
                    f.write(f"Likes: {comment['like_count']}\n")
                    if comment['is_reply']:
                        f.write("[REPLY]\n")
                    f.write(f"Text: {comment['text']}\n")
                    f.write("-" * 80 + "\n")
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        return str(output_path)
    
    def stream_comments(
        self, 
        url: str,
        max_comments: Optional[int] = None
    ) -> Generator[Comment, None, None]:
        """
        Stream comments one by one (memory efficient for large comment sections)
        
        Args:
            url: Video URL
            max_comments: Maximum number of comments to extract
            
        Yields:
            Comment objects
        """
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'getcomments': True,
            'socket_timeout': settings.DOWNLOAD_TIMEOUT_SECONDS,  # 5 minutes
        }
        
        if max_comments:
            ydl_opts['max_comments'] = max_comments
            ydl_opts['max_comment_count'] = max_comments
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            for comment_data in info.get('comments', []):
                yield self._parse_comment(comment_data)


def extract_comments_cli():
    """CLI entry point for comments extraction"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Extract comments from video URLs using yt-dlp',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract all comments from a YouTube video
  python comments_extractor.py "https://www.youtube.com/watch?v=VIDEO_ID"
  
  # Extract only top 100 comments
  python comments_extractor.py "URL" --max-comments 100
  
  # Save as text file instead of JSON
  python comments_extractor.py "URL" --format txt
  
  # Exclude reply comments
  python comments_extractor.py "URL" --no-replies
  
  # Custom output filename
  python comments_extractor.py "URL" --output "my_comments"
        """
    )
    
    parser.add_argument('url', help='Video URL to extract comments from')
    parser.add_argument(
        '--max-comments', '-n',
        type=int,
        default=None,
        help='Maximum number of comments to extract (default: all)'
    )
    parser.add_argument(
        '--no-replies',
        action='store_true',
        help='Exclude reply comments'
    )
    parser.add_argument(
        '--format', '-f',
        choices=['json', 'txt'],
        default='json',
        help='Output format (default: json)'
    )
    parser.add_argument(
        '--output', '-o',
        help='Custom output filename (without extension)'
    )
    parser.add_argument(
        '--output-dir',
        default='./extracted_comments',
        help='Directory to save comments (default: ./extracted_comments)'
    )
    
    args = parser.parse_args()
    
    extractor = CommentsExtractor(output_dir=args.output_dir)
    
    try:
        print(f"🔍 Extracting comments from: {args.url}")
        
        output_path = extractor.extract_and_save(
            url=args.url,
            output_filename=args.output,
            max_comments=args.max_comments,
            include_replies=not args.no_replies,
            format=args.format
        )
        
        print(f"✅ Comments extracted successfully!")
        print(f"📁 Saved to: {output_path}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}", file=__import__('sys').stderr)
        __import__('sys').exit(1)


if __name__ == "__main__":
    extract_comments_cli()
