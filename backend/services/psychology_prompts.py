def build_psychology_extraction_prompt(interval_seconds: int) -> str:
    return f"""
ROLE:
You are a behavioral psychology analyzer specialized in short-form video persuasion.

TASK:
Analyze the provided video and spoken transcript context. Return strictly valid JSON.

SEGMENTATION:
- Segment the video into contiguous {interval_seconds}-second intervals from start to end.
- Do not skip intervals.
- For each interval, keep analysis local to that segment.

ANALYZE:

1) Curiosity Narrative
- Calculate curiosity score (0-100), total open loops, avg loop duration (seconds).
- For each interval write a 30-50 word analytical paragraph covering:
  - whether curiosity is introduced/sustained/resolved
  - whether an open loop is created or maintained
  - how anticipation evolves in that segment
- Include interval intensity (0-100).

2) Persuasion Narrative
- Calculate persuasion score (0-100) and dominant signal across video.
- For each interval write a 30-50 word analytical paragraph covering:
  - dominant signal in that interval (Authority/Urgency/Social Proof/Certainty/Scarcity/None)
  - how influence is framed
  - likely psychological impact
- Include interval intensity (0-100).

3) Keep compatibility fields:
- curiosity (spikes/openLoops/closedLoops)
- emotional_arc
- tension_release
- persuasion_signals (numeric radar-style values)
- cognitive_load

OUTPUT FORMAT (JSON ONLY):
{{
  "curiosity_narrative": {{
    "interval_seconds": {interval_seconds},
    "curiosityScore": 0,
    "totalOpenLoops": 0,
    "avgLoopDuration": 0,
    "intervals": [
      {{ "start": 0, "end": {interval_seconds}, "narrative": "30-50 words", "intensity": 0 }}
    ]
  }},
  "persuasion_narrative": {{
    "interval_seconds": {interval_seconds},
    "persuasionScore": 0,
    "dominantSignal": "Authority|Urgency|Social Proof|Certainty|Scarcity|None",
    "intervals": [
      {{
        "start": 0,
        "end": {interval_seconds},
        "narrative": "30-50 words",
        "dominantSignal": "Authority|Urgency|Social Proof|Certainty|Scarcity|None",
        "intensity": 0
      }}
    ]
  }},
  "curiosity": {{
    "curiosityScore": 0,
    "spikes": [{{ "time": 0, "intensity": 0 }}],
    "openLoops": [{{ "time": 0, "text": "" }}],
    "closedLoops": [{{ "time": 0, "text": "" }}]
  }},
  "emotional_arc": {{
    "emotionalTimeline": [{{ "time": 0, "intensity": 0 }}],
    "highestPeak": {{ "time": 0, "value": 0 }},
    "strongestDrop": {{ "time": 0, "value": 0 }},
    "volatilityScore": 0
  }},
  "tension_release": {{
    "tensionCurve": [{{ "time": 0, "value": 0 }}],
    "releaseCurve": [{{ "time": 0, "value": 0 }}],
    "totalCycles": 0,
    "avgBuildDuration": 0,
    "unresolvedCount": 0
  }},
  "persuasion_signals": {{
    "authority": 0,
    "urgency": 0,
    "socialProof": 0,
    "certainty": 0,
    "scarcity": 0
  }},
  "cognitive_load": {{
    "cognitiveScore": 0,
    "densityTimeline": [{{ "time": 0, "density": 0 }}],
    "overloadDetected": false
  }}
}}

Hard requirements:
- Return only JSON.
- Do not include markdown fences.
- All scores/ints are clamped 0-100 unless otherwise specified.
- Narrative per interval must be 30-50 words.
- start/end/time are seconds from video start.
""".strip()
