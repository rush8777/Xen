"""
Statistics Generator - Main orchestration module
Coordinates analysis compaction, prompt generation, and LLM calls
"""

import json
import asyncio
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

from google.genai import types

try:
    from .statistics_extractor import analysis_compactor
    from .statistics_prompts import statistics_prompts
    from .statistics_cache_manager import statistics_cache_manager
    from .gemini_client import client
    from . import config
except ImportError:
    from statistics_extractor import analysis_compactor
    from statistics_prompts import statistics_prompts
    from statistics_cache_manager import statistics_cache_manager
    from gemini_client import client
    import config


class StatisticsGenerator:
    """
    Generates statistics from video analysis using optimized token usage.
    Reduces from ~110K tokens per component to ~500-3K tokens.
    """
    
    SCHEMA_VERSION = 1
    PROMPT_VERSION = "v2.0-optimized"  # Update when prompts change
    
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
    
    def __init__(self, output_dir: Path = None):
        self.output_dir = output_dir or config.OUTPUT_DIR
    
    async def generate_component_statistics(
        self,
        *,
        project_id: str,
        analysis_content: str,
        video_url: str,
        project_name: str,
        component_name: str,
        use_cache: bool = True,
    ) -> Dict[str, Any]:
        """
        Generate statistics for a single component.
        
        Args:
            project_id: Project identifier
            analysis_content: Full video analysis text
            video_url: Video URL
            project_name: Project name
            component_name: Component to generate (e.g., "sentiment_pulse")
            use_cache: Whether to use cached results
            
        Returns:
            Dictionary with component statistics
        """
        
        # Step 1: Check cache
        if use_cache:
            cache_key = statistics_cache_manager.calculate_component_hash(
                analysis_content=analysis_content,
                video_url=video_url,
                project_name=project_name,
                component_name=component_name,
                schema_version=self.SCHEMA_VERSION,
                prompt_version=self.PROMPT_VERSION,
            )
            
            cached = statistics_cache_manager.get_cached_component(cache_key)
            if cached:
                output_path = Path(cached['output_path'])
                if output_path.exists():
                    with open(output_path, 'r') as f:
                        return json.load(f)
        
        # Step 2: Compact analysis data (110K → 500-3K tokens)
        compact_data = analysis_compactor.extract_for_component(
            analysis_content,
            component_name
        )
        
        print(f"  📊 {component_name}")
        print(f"     Original: ~{len(analysis_content)} chars")
        print(f"     Compacted: ~{len(compact_data)} chars")
        print(f"     Reduction: {100 * (1 - len(compact_data)/len(analysis_content)):.1f}%")
        
        # Step 3: Generate prompt
        prompt = statistics_prompts.build_prompt(
            component_name,
            compact_data,
            video_url,
            project_name
        )
        
        # Step 4: Call LLM
        try:
            response = await self._call_gemini(prompt)
            result_data = self._parse_json_response(response)
            
            # Step 5: Save to file
            output_path = self._save_component_result(
                project_id,
                component_name,
                result_data
            )
            
            # Step 6: Cache the result
            if use_cache:
                statistics_cache_manager.save_cached_component(
                    cache_key,
                    component_name=component_name,
                    output_path=output_path,
                    schema_version=self.SCHEMA_VERSION,
                    prompt_version=self.PROMPT_VERSION,
                )
            
            return result_data
            
        except Exception as e:
            print(f"     ❌ Error: {str(e)}")
            # Return default payload on error
            return self._default_component_payload(component_name)
    
    async def generate_all_statistics(
        self,
        *,
        project_id: str,
        analysis_content: str,
        video_url: str,
        project_name: str,
        use_cache: bool = True,
    ) -> Dict[str, Any]:
        """
        Generate all statistics components for a video.
        
        Returns:
            Dictionary with all component results
        """
        print(f"\n📊 Generating statistics for project {project_id}")
        print(f"   Video: {video_url}")
        print(f"   Analysis size: {len(analysis_content)} chars\n")
        
        results = {}
        
        # Generate all components
        for component_name in self.COMPONENT_NAMES:
            try:
                result = await self.generate_component_statistics(
                    project_id=project_id,
                    analysis_content=analysis_content,
                    video_url=video_url,
                    project_name=project_name,
                    component_name=component_name,
                    use_cache=use_cache,
                )
                results[component_name] = result
                
            except Exception as e:
                print(f"  ❌ {component_name}: {str(e)}")
                results[component_name] = self._default_component_payload(component_name)
        
        print(f"\n✅ Statistics generation complete")
        return results
    
    async def _call_gemini(self, prompt: str) -> str:
        """Call Gemini API with the prompt"""
        try:
            # Use Gemini 2.5 Flash for fast, cheap statistics generation
            response = client.models.generate_content(
                model="models/gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.2,
                    response_mime_type="application/json",
                ),
            )

            return response.text or ""

        except Exception as e:
            raise Exception(f"Gemini API error: {str(e)}")
    
    def _parse_json_response(self, response_text: str) -> Any:
        """Parse JSON from LLM response, handling markdown code blocks"""
        try:
            # Remove markdown code blocks if present
            cleaned = response_text.strip()
            if cleaned.startswith("```"):
                # Remove ```json and ``` wrappers
                lines = cleaned.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                cleaned = "\n".join(lines)
            
            return json.loads(cleaned)
            
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse JSON response: {str(e)}\nResponse: {response_text[:500]}")
    
    def _save_component_result(
        self,
        project_id: str,
        component_name: str,
        data: Any
    ) -> Path:
        """Save component result to file"""
        # Create output directory for this project
        project_dir = self.output_dir / str(project_id) / "statistics"
        project_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%SZ")
        filename = f"{component_name}.v{self.SCHEMA_VERSION}.{timestamp}.json"
        output_path = project_dir / filename
        
        # Save JSON
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        return output_path
    
    def _default_component_payload(self, component_name: str) -> Any:
        """Return default/empty payload for a component"""
        if component_name == "video_metrics_grid":
            return {
                "net_sentiment_score": 50,
                "net_sentiment_delta_vs_last": 0,
                "engagement_velocity_comments_per_hour": 10,
                "toxicity_alert_bots_detected": 0,
                "question_density_percent": 0,
            }
        return []


# Global instance
statistics_generator = StatisticsGenerator()


# CLI interface
async def main():
    """CLI for testing statistics generation"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate video statistics")
    parser.add_argument("analysis_file", type=Path, help="Path to video analysis text file")
    parser.add_argument("--project-id", default="test", help="Project ID")
    parser.add_argument("--video-url", default="https://example.com/video", help="Video URL")
    parser.add_argument("--project-name", default="Test Project", help="Project name")
    parser.add_argument("--component", help="Generate only this component")
    
    args = parser.parse_args()
    
    # Load analysis
    with open(args.analysis_file, 'r') as f:
        analysis_content = f.read()
    
    # Generate statistics
    if args.component:
        result = await statistics_generator.generate_component_statistics(
            project_id=args.project_id,
            analysis_content=analysis_content,
            video_url=args.video_url,
            project_name=args.project_name,
            component_name=args.component,
        )
        print(json.dumps(result, indent=2))
    else:
        results = await statistics_generator.generate_all_statistics(
            project_id=args.project_id,
            analysis_content=analysis_content,
            video_url=args.video_url,
            project_name=args.project_name,
        )
        print(json.dumps(results, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
