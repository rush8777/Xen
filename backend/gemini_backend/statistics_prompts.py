"""
Statistics Prompts - Optimized for compact analysis data
Uses intelligent inference instead of requiring explicit mentions
"""

from typing import Any


class StatisticsPrompts:
    """Generates prompts for statistics extraction with intelligent inference"""
    
    def _create_prompt_video_metrics_grid(self, compact_data: str, video_url: str, project_name: str) -> str:
        data_section = f"""
COMPACT ANALYSIS DATA:
{compact_data}
""" if compact_data else """
NOTE: You are analyzing the video directly via cached content. Use the video visuals and on-screen text to infer metrics.
"""
        return f"""
SYSTEM ROLE:
You are an advanced video content analyzer that infers engagement metrics
from visual and textual evidence in video analysis data.

VIDEO CONTEXT:
URL: {video_url}
PROJECT: {project_name}
{data_section}

REQUIRED OUTPUT SCHEMA (RETURN ONLY VALID JSON, NO MARKDOWN):
{{
  "net_sentiment_score": <integer 0-100>,
  "net_sentiment_delta_vs_last": <integer -100 to 100>,
  "engagement_velocity_comments_per_hour": <integer>,
  "toxicity_alert_bots_detected": <integer>,
  "question_density_percent": <integer 0-100>
}}

INTELLIGENT ANALYSIS RULES:

1. **net_sentiment_score** (0-100):
   - Analyze the video's tone, text overlays, and messaging
   - Philosophical/inspirational content: 70-85
   - Social/bar conversations: 50-65
   - Neutral informational: 50-60
   - Controversial/negative: 20-40
   - Consider text sentiment, visual mood, and overall message

2. **net_sentiment_delta_vs_last** (-100 to 100):
   - If no historical data exists, return 0
   - For first-time analysis, return 0

3. **engagement_velocity_comments_per_hour**:
   - Estimate based on video type and platform context
   - Philosophical short-form (TikTok/Reels): 30-80/hour
   - Social/bar conversation: 15-40/hour
   - YouTube educational: 5-20/hour
   - Nature/calm content: 5-15/hour
   - Controversial topics: 50-200/hour

4. **toxicity_alert_bots_detected**:
   - Philosophical/neutral content: 0-1
   - Social conversation: 0-2
   - Polarizing topics: 5-15
   - Default: 0

5. **question_density_percent** (0-100):
   - Count questions in text overlays ("What if", "who are you", "?")
   - Calculate: (question texts / total texts) * 100
   - Philosophical questioning videos: 40-70%
   - Informational: 10-30%
   - Entertainment: 5-20%

OUTPUT REQUIREMENTS:
- Always return valid JSON with all 5 fields (no markdown code blocks)
- Use contextual reasoning when exact data unavailable
- Base estimates on content type and tone
- Never return empty {{}}
"""

    def _create_prompt_sentiment_pulse(self, compact_data: str, video_url: str, project_name: str) -> str:
        return f"""
SYSTEM ROLE:
You are a time-series sentiment analyzer for video content.
You map sentiment to video timestamps based on textual content and tone.

VIDEO CONTEXT:
URL: {video_url}
PROJECT: {project_name}

TEXT TIMELINE DATA:
{compact_data}

REQUIRED OUTPUT SCHEMA (RETURN ONLY JSON, NO MARKDOWN):
[
  {{ "time": "MM:SS", "positive": <integer 0-100>, "negative": <integer 0-100> }}
]

INTELLIGENT ANALYSIS RULES:

1. **Extract timestamps** from the text timeline data provided
2. **For each timestamp**, analyze the text content:
   - Inspirational text = high positive (70-90), low negative (5-15)
   - Questioning text = medium positive (40-60), medium negative (20-40)
   - Dark/heavy text = low positive (20-40), high negative (50-70)
   - Neutral text = balanced (50 positive, 20 negative)

3. **Sentiment scoring**:
   - Positive (0-100): Uplifting, hopeful, inspirational messages
   - Negative (0-100): Challenging, heavy, critical topics
   - Both can overlap for complex emotions

4. **Generate 6-10 data points** evenly distributed across video duration

EXAMPLE OUTPUT:
[
  {{ "time": "00:00", "positive": 60, "negative": 15 }},
  {{ "time": "00:10", "positive": 75, "negative": 10 }},
  {{ "time": "00:20", "positive": 80, "negative": 20 }},
  {{ "time": "00:30", "positive": 70, "negative": 25 }}
]

OUTPUT REQUIREMENTS:
- Generate at least 6 data points
- Use timestamps from the provided data
- Never return []
- Return only JSON (no markdown code blocks)
"""

    def _create_prompt_emotion_radar(self, compact_data: str, video_url: str, project_name: str) -> str:
        return f"""
SYSTEM ROLE:
You are an emotional tone analyzer for video content.
You identify dominant emotional themes based on content type and messaging.

VIDEO CONTEXT:
URL: {video_url}
PROJECT: {project_name}

COMPACT DATA:
{compact_data}

REQUIRED OUTPUT (JSON ONLY, NO MARKDOWN):
[
  {{ "subject": "Hype", "value": <integer 0-100> }},
  {{ "subject": "Confusion", "value": <integer 0-100> }},
  {{ "subject": "Excitement", "value": <integer 0-100> }},
  {{ "subject": "Criticism", "value": <integer 0-100> }},
  {{ "subject": "Support", "value": <integer 0-100> }}
]

INTELLIGENT ANALYSIS RULES:

Based on content type, assign emotional distribution:

**Philosophical/Existential content**:
- Hype: 25-35 (moderate viral potential)
- Confusion: 60-75 (high, due to deep questions)
- Excitement: 65-80 (inspirational messaging)
- Criticism: 10-20 (low, positive reception)
- Support: 70-85 (high agreement)

**Social/Bar conversation**:
- Hype: 30-45
- Confusion: 20-35
- Excitement: 40-55
- Criticism: 25-40
- Support: 50-65

**Nature/Calm content**:
- Hype: 15-25
- Confusion: 10-20
- Excitement: 30-45
- Criticism: 5-15
- Support: 60-75

**Educational content**:
- Hype: 20-30
- Confusion: 30-45
- Excitement: 50-65
- Criticism: 15-25
- Support: 65-80

CONTEXT CLUES:
- Text with "universe", "consciousness" → Philosophical
- Text with "what if", questioning → High Confusion
- Inspirational tone → High Support, High Excitement
- Social setting → Balanced emotions

OUTPUT REQUIREMENTS:
- All values must sum to 250-350 (not necessarily 100)
- Base on content analysis
- Never return []
- Return only JSON (no markdown)
"""

    def _create_prompt_emotional_intensity_timeline(self, compact_data: str, video_url: str, project_name: str) -> str:
        return f"""
SYSTEM ROLE:
You map emotional intensity across video timeline.
You identify peaks and valleys in emotional engagement.

VIDEO CONTEXT:
URL: {video_url}
PROJECT: {project_name}

DATA:
{compact_data}

REQUIRED OUTPUT (JSON ONLY, NO MARKDOWN):
[
  {{ "time": "MM:SS", "intensity": <integer 0-100>, "emotion": "neutral|excited|confused|critical" }}
]

INTELLIGENT ANALYSIS RULES:

1. **Extract timestamps** from the data
2. **For each timestamp**, analyze text and tone:
   
   **Intensity scoring** (0-100):
   - 0-25: Very calm, minimal engagement
   - 25-45: Gentle, thoughtful content
   - 45-65: Moderate emotional presence
   - 65-85: Strong emotional engagement
   - 85-100: Peak intensity, climactic moments
   
   **Emotion classification**:
   - **neutral**: Calm, factual, observational
   - **excited**: Inspirational, uplifting, "universe" themes
   - **confused**: Questioning, "what if", philosophical uncertainty  
   - **critical**: Challenging, confrontational, negative

3. **Mapping examples**:
   - "What if I told you" → confused, intensity 55
   - "You are the universe" → excited, intensity 80
   - Calm forest visuals → neutral, intensity 30
   - Deep philosophical question → confused, intensity 70

OUTPUT REQUIREMENTS:
- Generate 8-12 data points across video
- Use actual timestamps from data
- Vary intensity based on message weight
- Never return []
- Return only JSON (no markdown)
"""

    def _create_prompt_audience_age_distribution(self, compact_data: str, video_url: str, project_name: str) -> str:
        return f"""
SYSTEM ROLE:
You estimate likely age distribution based on video content type.

VIDEO CONTEXT:
URL: {video_url}
PROJECT: {project_name}

METADATA:
{compact_data}

REQUIRED OUTPUT (JSON ONLY, NO MARKDOWN):
[
  {{ "label": "13–17", "value": <integer 0-100> }},
  {{ "label": "18–24", "value": <integer 0-100> }},
  {{ "label": "25–34", "value": <integer 0-100> }},
  {{ "label": "35–44", "value": <integer 0-100> }},
  {{ "label": "45+", "value": <integer 0-100> }}
]

DISTRIBUTION BY CONTENT TYPE:

**Philosophical/Existential**:
[
  {{ "label": "13–17", "value": 12 }},
  {{ "label": "18–24", "value": 38 }},
  {{ "label": "25–34", "value": 32 }},
  {{ "label": "35–44", "value": 14 }},
  {{ "label": "45+", "value": 4 }}
]

**Social/Bar conversation**:
[
  {{ "label": "13–17", "value": 3 }},
  {{ "label": "18–24", "value": 28 }},
  {{ "label": "25–34", "value": 42 }},
  {{ "label": "35–44", "value": 22 }},
  {{ "label": "45+", "value": 5 }}
]

**Educational**:
[
  {{ "label": "13–17", "value": 22 }},
  {{ "label": "18–24", "value": 40 }},
  {{ "label": "25–34", "value": 26 }},
  {{ "label": "35–44", "value": 10 }},
  {{ "label": "45+", "value": 2 }}
]

**Nature/Calm**:
[
  {{ "label": "13–17", "value": 8 }},
  {{ "label": "18–24", "value": 25 }},
  {{ "label": "25–34", "value": 35 }},
  {{ "label": "35–44", "value": 22 }},
  {{ "label": "45+", "value": 10 }}
]

OUTPUT REQUIREMENTS:
- Values must sum to 100
- Select distribution matching content type
- Never return []
- Return only JSON (no markdown)
"""

    def _create_prompt_audience_gender_distribution(self, compact_data: str, video_url: str, project_name: str) -> str:
        return f"""
SYSTEM ROLE:
You estimate gender distribution based on content analysis.

VIDEO CONTEXT:
URL: {video_url}
PROJECT: {project_name}

METADATA:
{compact_data}

REQUIRED OUTPUT (JSON ONLY, NO MARKDOWN):
[
  {{ "label": "Male", "value": <integer 0-100> }},
  {{ "label": "Female", "value": <integer 0-100> }},
  {{ "label": "Other / Unknown", "value": <integer 0-100> }}
]

DISTRIBUTION BY CONTENT TYPE:

**Philosophical/Spiritual**: Balanced
{{ "Male": 48, "Female": 48, "Other / Unknown": 4 }}

**Social/Bar**: Slightly male-skewed
{{ "Male": 54, "Female": 43, "Other / Unknown": 3 }}

**Nature/Calm**: Balanced
{{ "Male": 46, "Female": 50, "Other / Unknown": 4 }}

**Educational**: Balanced
{{ "Male": 51, "Female": 46, "Other / Unknown": 3 }}

OUTPUT REQUIREMENTS:
- Values must sum to 100
- Base on content type
- Never return []
- Return only JSON (no markdown)
"""

    def _create_prompt_audience_top_locations(self, compact_data: str, video_url: str, project_name: str) -> str:
        return f"""
SYSTEM ROLE:
You estimate geographic distribution based on content and language.

VIDEO CONTEXT:
URL: {video_url}
PROJECT: {project_name}

METADATA:
{compact_data}

REQUIRED OUTPUT (JSON ONLY, NO MARKDOWN):
[
  {{ "label": "Country", "value": <integer 0-100> }}
]

DEFAULT ENGLISH CONTENT DISTRIBUTION:
[
  {{ "label": "United States", "value": 42 }},
  {{ "label": "United Kingdom", "value": 14 }},
  {{ "label": "Canada", "value": 11 }},
  {{ "label": "Australia", "value": 9 }},
  {{ "label": "India", "value": 13 }},
  {{ "label": "Other", "value": 11 }}
]

PHILOSOPHICAL CONTENT (more global):
[
  {{ "label": "United States", "value": 32 }},
  {{ "label": "United Kingdom", "value": 12 }},
  {{ "label": "India", "value": 18 }},
  {{ "label": "Canada", "value": 9 }},
  {{ "label": "Germany", "value": 8 }},
  {{ "label": "Brazil", "value": 7 }},
  {{ "label": "Other", "value": 14 }}
]

OUTPUT REQUIREMENTS:
- Return 5-7 locations
- Values sum to 100
- Never return []
- Return only JSON (no markdown)
"""

    def _create_prompt_audience_interests(self, compact_data: str, video_url: str, project_name: str) -> str:
        return f"""
SYSTEM ROLE:
You identify likely audience interests based on video content.

VIDEO CONTEXT:
URL: {video_url}
PROJECT: {project_name}

METADATA:
{compact_data}

REQUIRED OUTPUT (JSON ONLY, NO MARKDOWN):
[
  "Interest1",
  "Interest2",
  "Interest3"
]

INTERESTS BY CONTENT TYPE:

**Philosophical/Existential**:
["Philosophy", "Spirituality", "Psychology", "Meditation", "Self-improvement", "Consciousness"]

**Social/Bar**:
["Nightlife", "Social Culture", "Relationships", "Lifestyle", "Urban Life"]

**Nature/Calm**:
["Nature", "Mindfulness", "Meditation", "Environmental", "Wellness", "Travel"]

**Educational**:
["Education", "Learning", "Science", "Documentary", "Knowledge"]

OUTPUT REQUIREMENTS:
- Return 4-6 interests
- Use title case
- Match content type
- Never return []
- Return only JSON (no markdown)
"""

    def _create_prompt_top_comments(self, compact_data: str, video_url: str, project_name: str) -> str:
        return f"""
SYSTEM ROLE:
You generate realistic representative comments based on video content.

VIDEO CONTEXT:
URL: {video_url}
PROJECT: {project_name}

CONTENT INFO:
{compact_data}

REQUIRED OUTPUT (JSON ONLY, NO MARKDOWN):
[
  {{
    "id": "c001",
    "author": "username",
    "avatar": "US",
    "content": "realistic comment text",
    "likes": <integer>,
    "intent": "positive|criticism|question"
  }}
]

GENERATION RULES:

Generate 6-8 realistic comments matching the video's tone.

**Intent Distribution**:
- 50-60% positive
- 25-35% questions  
- 10-20% criticism

**Metadata**:
- IDs: "c001", "c002", etc.
- Authors: Realistic usernames (e.g., "alex_m", "deep_thinker", "sarah_k")
- Avatars: First 2 letters uppercase (e.g., "AL", "DE", "SA")
- Likes: Top comment 800-2500, others 50-800

**For Philosophical content**:
[
  {{
    "id": "c001",
    "author": "cosmic_wanderer",
    "avatar": "CO",
    "content": "This perspective just changed how I see reality 🌌",
    "likes": 1847,
    "intent": "positive"
  }},
  {{
    "id": "c002",
    "author": "deep_thinker",
    "avatar": "DE",
    "content": "Wait so are we living infinite lives simultaneously or sequentially?",
    "likes": 923,
    "intent": "question"
  }},
  {{
    "id": "c003",
    "author": "mindful_soul",
    "avatar": "MI",
    "content": "Beautiful way to think about consciousness and existence",
    "likes": 654,
    "intent": "positive"
  }},
  {{
    "id": "c004",
    "author": "skeptic_mind",
    "avatar": "SK",
    "content": "Interesting philosophy but lacks scientific basis",
    "likes": 187,
    "intent": "criticism"
  }},
  {{
    "id": "c005",
    "author": "wisdom_seeker",
    "avatar": "WI",
    "content": "Sending this to everyone who's been questioning their purpose",
    "likes": 412,
    "intent": "positive"
  }}
]

**For Social/Bar content**:
Generate conversational, relatable comments about social situations.

**For Nature content**:
Generate appreciative, calming comments about visuals.

OUTPUT REQUIREMENTS:
- Generate 6-8 comments
- Match video tone
- Realistic usernames
- Never return []
- Return only JSON (no markdown)
"""

    def build_prompt(self, component_name: str, compact_data: str, video_url: str, project_name: str) -> str:
        """Build the appropriate prompt for the component"""
        
        # When compact_data is empty, we're using cached video - add a note to prompts
        if not compact_data:
            # Add instruction to use cached video content directly
            video_note = "\n\nNOTE: You are analyzing the video directly via cached content. Use the video visuals, on-screen text, and visual elements to perform the analysis.\n"
        else:
            video_note = ""
        
        if component_name == "video_metrics_grid":
            prompt = self._create_prompt_video_metrics_grid(compact_data, video_url, project_name)
        elif component_name == "sentiment_pulse":
            prompt = self._create_prompt_sentiment_pulse(compact_data, video_url, project_name)
        elif component_name == "emotion_radar":
            prompt = self._create_prompt_emotion_radar(compact_data, video_url, project_name)
        elif component_name == "emotional_intensity_timeline":
            prompt = self._create_prompt_emotional_intensity_timeline(compact_data, video_url, project_name)
        elif component_name == "audience_demographics.age_distribution":
            prompt = self._create_prompt_audience_age_distribution(compact_data, video_url, project_name)
        elif component_name == "audience_demographics.gender_distribution":
            prompt = self._create_prompt_audience_gender_distribution(compact_data, video_url, project_name)
        elif component_name == "audience_demographics.top_locations":
            prompt = self._create_prompt_audience_top_locations(compact_data, video_url, project_name)
        elif component_name == "audience_demographics.audience_interests":
            prompt = self._create_prompt_audience_interests(compact_data, video_url, project_name)
        elif component_name == "top_comments":
            prompt = self._create_prompt_top_comments(compact_data, video_url, project_name)
        else:
            raise ValueError(f"Unknown statistics component: {component_name}")
        
        # Append video note if using cached content
        if video_note:
            prompt = prompt.rstrip() + video_note
        
        return prompt


# Global instance
statistics_prompts = StatisticsPrompts()
