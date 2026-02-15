"""
Statistics Extractor - Optimized for minimal token usage
Extracts compact summaries from full video analysis for statistics generation
"""

import re
import json
from typing import Dict, List, Any, Tuple
from pathlib import Path


class AnalysisCompactor:
    """
    Extracts only relevant portions of video analysis for each statistics component.
    Reduces token usage from ~110K to ~500-3000 tokens per component.
    """
    
    def extract_text_overlays_timeline(self, analysis: str) -> str:
        """
        Extract text overlays with timestamps for sentiment/emotion analysis.
        Reduces 110K tokens to ~1-2K tokens.
        """
        intervals = self._parse_intervals(analysis)
        
        extracted = ["TEXT OVERLAY TIMELINE:\n"]
        for interval in intervals:
            start_time = interval['start']
            end_time = interval['end']
            
            # Extract just TEXT & SYMBOLS section
            text_section = self._extract_section(interval['content'], "TEXT & SYMBOLS")
            
            if text_section:
                # Extract actual text content, limit to 300 chars
                text_content = self._extract_displayed_text(text_section)
                if text_content:
                    extracted.append(f"[{start_time}] {text_content}")
        
        return "\n".join(extracted)
    
    def extract_visual_tone_summary(self, analysis: str) -> str:
        """
        Extract lighting, color, and mood indicators.
        Reduces 110K tokens to ~800 tokens.
        """
        intervals = self._parse_intervals(analysis)
        
        extracted = ["VISUAL TONE SUMMARY:\n"]
        for interval in intervals:
            lighting = self._extract_section(interval['content'], "LIGHTING & COLOR")
            
            if lighting:
                # Get key mood indicators (first 200 chars)
                mood = lighting[:200].strip()
                extracted.append(f"[{interval['start']}] {mood}")
        
        return "\n".join(extracted)
    
    def extract_video_metadata(self, analysis: str) -> Dict[str, Any]:
        """
        Extract high-level video metadata for demographics estimation.
        Reduces 110K tokens to ~300 tokens.
        """
        # Get first interval for environment info
        intervals = self._parse_intervals(analysis)
        if not intervals:
            return {}
        
        first_interval = intervals[0]
        
        environment = self._extract_section(first_interval['content'], "ENVIRONMENT & BACKGROUND")
        people = self._extract_section(first_interval['content'], "PEOPLE / HUMAN FIGURES")
        text_samples = []
        
        # Collect text from first 3 intervals
        for interval in intervals[:3]:
            text = self._extract_section(interval['content'], "TEXT & SYMBOLS")
            if text:
                text_samples.append(self._extract_displayed_text(text))
        
        # Detect content type
        content_type = self._detect_content_type(environment, text_samples)
        
        return {
            "content_type": content_type,
            "setting": self._extract_setting(environment),
            "has_people": "no people" not in people.lower() if people else False,
            "text_themes": text_samples[:5],
            "total_intervals": len(intervals)
        }
    
    def extract_for_component(self, analysis_content: str, component_name: str) -> str:
        """
        Extract only the data needed for a specific component.
        Main entry point for reducing token usage.
        """
        if component_name == "video_metrics_grid":
            # Need: text overlays + visual tone
            metadata = self.extract_video_metadata(analysis_content)
            text_timeline = self.extract_text_overlays_timeline(analysis_content)
            
            return f"""VIDEO METADATA:
{json.dumps(metadata, indent=2)}

{text_timeline[:1000]}
"""
        
        elif component_name == "sentiment_pulse":
            # Need: text timeline with timestamps
            return self.extract_text_overlays_timeline(analysis_content)
        
        elif component_name == "emotion_radar":
            # Need: text content + visual tone
            metadata = self.extract_video_metadata(analysis_content)
            text = self.extract_text_overlays_timeline(analysis_content)
            tone = self.extract_visual_tone_summary(analysis_content)
            
            return f"""CONTENT TYPE: {metadata['content_type']}

{text[:800]}

{tone[:400]}
"""
        
        elif component_name == "emotional_intensity_timeline":
            # Need: text + tone with timestamps
            text = self.extract_text_overlays_timeline(analysis_content)
            tone = self.extract_visual_tone_summary(analysis_content)
            
            return f"""{text[:1500]}

TONE:
{tone[:500]}
"""
        
        elif component_name.startswith("audience_demographics"):
            # Just need high-level metadata
            metadata = self.extract_video_metadata(analysis_content)
            return f"""VIDEO METADATA FOR DEMOGRAPHICS:
{json.dumps(metadata, indent=2)}
"""
        
        elif component_name == "top_comments":
            # Need content type and themes
            metadata = self.extract_video_metadata(analysis_content)
            return f"""GENERATE COMMENTS BASED ON:
Content Type: {metadata['content_type']}
Setting: {metadata['setting']}
Themes: {', '.join(metadata.get('text_themes', [])[:3])}
"""
        
        # Default: return compact summary
        return self._create_compact_summary(analysis_content)
    
    def _parse_intervals(self, analysis: str) -> List[Dict[str, Any]]:
        """Parse interval blocks from analysis"""
        # Match intervals like [00:00–00:05]
        interval_pattern = r'\[(\d{2}:\d{2})–(\d{2}:\d{2})\]'
        parts = re.split(interval_pattern, analysis)
        
        intervals = []
        i = 1
        while i < len(parts):
            if i + 2 < len(parts):
                intervals.append({
                    'start': parts[i],
                    'end': parts[i+1],
                    'content': parts[i+2]
                })
                i += 3
            else:
                break
        
        return intervals
    
    def _extract_section(self, content: str, section_name: str) -> str:
        """Extract a specific numbered section from interval content"""
        # Match section headers like "5. TEXT & SYMBOLS"
        pattern = rf'\d+\.\s+{re.escape(section_name)}(.*?)(?=\d+\.|$)'
        match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
        
        if match:
            return match.group(1).strip()
        return ""
    
    def _extract_displayed_text(self, text_section: str) -> str:
        """Extract actual displayed text from TEXT & SYMBOLS section"""
        # Look for quoted text or "the text reads" patterns
        texts = []
        
        # Pattern 1: "text" or 'text'
        quoted = re.findall(r'["\']([^"\']{3,100})["\']', text_section)
        texts.extend(quoted[:5])
        
        # Pattern 2: "The text displays: X" or "showing the text X"
        display_patterns = [
            r'text (?:reads|displays?|shows?|states?):?\s*["\']?([^."\n]{5,100})["\']?',
            r'visible (?:as|is):?\s*["\']?([^."\n]{5,100})["\']?',
        ]
        
        for pattern in display_patterns:
            matches = re.findall(pattern, text_section, re.IGNORECASE)
            texts.extend(matches[:3])
        
        return " | ".join(texts[:8]) if texts else ""
    
    def _detect_content_type(self, environment: str, text_samples: List[str]) -> str:
        """Detect video content type from environment and text"""
        env_lower = environment.lower() if environment else ""
        text_combined = " ".join(text_samples).lower()
        
        # Check for philosophical/spiritual content
        if any(word in text_combined for word in ['universe', 'consciousness', 'existence', 'soul', 'what if']):
            return "philosophical"
        
        # Check for bar/social setting
        if any(word in env_lower for word in ['bar', 'club', 'restaurant', 'bottles']):
            return "social"
        
        # Check for nature/forest
        if any(word in env_lower for word in ['forest', 'trees', 'nature', 'outdoor']):
            return "nature"
        
        # Check for educational
        if any(word in text_combined for word in ['learn', 'tutorial', 'how to', 'lesson']):
            return "educational"
        
        return "general"
    
    def _extract_setting(self, environment: str) -> str:
        """Extract brief setting description"""
        if not environment:
            return "unknown"
        
        # Get first sentence or first 100 chars
        first_sentence = re.split(r'[.!?]', environment)[0]
        return first_sentence[:100].strip()
    
    def _create_compact_summary(self, analysis: str) -> str:
        """Create a general compact summary (fallback)"""
        intervals = self._parse_intervals(analysis)
        
        metadata = self.extract_video_metadata(analysis)
        text = self.extract_text_overlays_timeline(analysis)
        
        return f"""COMPACT SUMMARY:
Total Duration: {len(intervals) * 5}s
Content Type: {metadata['content_type']}
Setting: {metadata['setting']}

{text[:1000]}
"""


# Global instance
analysis_compactor = AnalysisCompactor()
