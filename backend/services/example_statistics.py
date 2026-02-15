#!/usr/bin/env python3
"""
Example: Generate Statistics from Video Analysis
Demonstrates the optimized statistics generation system
"""

import asyncio
from pathlib import Path
import json

# Import the statistics system
from statistics_generator import statistics_generator


async def example_single_component():
    """Example: Generate a single component"""
    print("=" * 70)
    print("EXAMPLE 1: Generate Single Component")
    print("=" * 70)
    
    # Sample analysis text (in practice, this comes from video analysis)
    sample_analysis = """
[00:00–00:05]
INTERVAL: 00:00 – 00:05

5. TEXT & SYMBOLS
   The text "What if I told you" appears at the top of the screen in white font.
   Below it, "this life is not" appears in white font.

7. LIGHTING & COLOR
   The scene is brightly lit with soft, diffused lighting suggesting daylight.
   Dominant colors are vibrant greens from forest foliage.

[00:05–00:10]
5. TEXT & SYMBOLS
   The text "you've chosen." appears in white font.
   
[00:10–00:15]
5. TEXT & SYMBOLS
   The text "You are the universe experiencing itself." appears.
"""
    
    # Generate sentiment pulse component
    result = await statistics_generator.generate_component_statistics(
        project_id="example_001",
        analysis_content=sample_analysis,
        video_url="https://youtube.com/example",
        project_name="Philosophical Video",
        component_name="sentiment_pulse"
    )
    
    print("\nResult:")
    print(json.dumps(result, indent=2))


async def example_all_components():
    """Example: Generate all components"""
    print("\n" + "=" * 70)
    print("EXAMPLE 2: Generate All Components")
    print("=" * 70)
    
    # Load a real analysis file if available
    analysis_files = list(Path("outputs").glob("**/*.txt"))
    
    if analysis_files:
        analysis_file = analysis_files[0]
        print(f"\nUsing analysis file: {analysis_file}")
        
        with open(analysis_file, 'r') as f:
            analysis_content = f.read()
    else:
        print("\nNo analysis files found, using sample data")
        analysis_content = """
[00:00–00:05]
INTERVAL: 00:00 – 00:05

1. CAMERA & FRAME
   Static camera, medium shot of forest scene.

2. ENVIRONMENT & BACKGROUND
   Dense forest with tall trees and green foliage.

5. TEXT & SYMBOLS
   Text overlay: "What if I told you this life is not you've chosen"

7. LIGHTING & COLOR
   Bright, diffused lighting. Dominant green colors from trees.

[00:05–00:10]
5. TEXT & SYMBOLS
   Text: "You are the universe experiencing itself."
"""
    
    # Generate all statistics
    all_stats = await statistics_generator.generate_all_statistics(
        project_id="example_002",
        analysis_content=analysis_content,
        video_url="https://youtube.com/watch?v=example",
        project_name="Example Project"
    )
    
    print("\n✅ Generated components:")
    for component_name, data in all_stats.items():
        print(f"   - {component_name}")
    
    # Show some results
    print("\nSample results:")
    print("\n1. Video Metrics:")
    print(json.dumps(all_stats.get('video_metrics_grid', {}), indent=2))
    
    print("\n2. Sentiment Pulse (first 3 points):")
    sentiment = all_stats.get('sentiment_pulse', [])
    print(json.dumps(sentiment[:3], indent=2))
    
    print("\n3. Top Comments (first 2):")
    comments = all_stats.get('top_comments', [])
    print(json.dumps(comments[:2], indent=2))


async def example_token_comparison():
    """Example: Show token usage comparison"""
    print("\n" + "=" * 70)
    print("EXAMPLE 3: Token Usage Comparison")
    print("=" * 70)
    
    # Sample full analysis
    full_analysis = """
[00:00–00:05]
INTERVAL: 00:00 – 00:05

1. CAMERA & FRAME
    The camera remains static throughout this interval, maintaining a fixed perspective on the scene. The framing is a medium shot, centered on a large tree trunk, with surrounding foliage filling the majority of the vertical frame. The video is presented in a portrait orientation, typical for mobile viewing. An on-screen overlay displaying the text "VEED" is positioned at the top center of the frame. Additional white text overlays appear sequentially in the mid-frame, presenting phrases from a narrative. The overall composition is stable, with no panning, zooming, or tilting movements detected. The edges of the frame clearly define the visible area, with no visible UI elements beyond the mentioned text overlays.

2. ENVIRONMENT & BACKGROUND
    The physical setting is a natural outdoor environment, specifically a forest or wooded area. The ground in the foreground and midground is covered with a mix of green grass and patches of lighter, yellowish-brown vegetation, possibly dry grass or exposed earth. Several trees are visible, with a prominent, tall tree trunk centrally located. Denser green foliage from numerous trees forms the background and flanks the central tree on both sides. The background appears somewhat hazy or misty, creating a soft, diffused effect that obscures distant details. Small, light-colored rocks are scattered across the ground in the foreground and midground, adding texture to the terrain.

[continues for many more intervals...]
""" * 20  # Simulate long analysis
    
    from statistics_extractor import analysis_compactor
    
    print(f"\nFull analysis size: {len(full_analysis):,} characters")
    print(f"Estimated tokens: ~{len(full_analysis) // 4:,} tokens")
    
    # Extract compact data
    compact = analysis_compactor.extract_for_component(
        full_analysis,
        "sentiment_pulse"
    )
    
    print(f"\nCompact data size: {len(compact):,} characters")
    print(f"Estimated tokens: ~{len(compact) // 4:,} tokens")
    
    reduction = 100 * (1 - len(compact) / len(full_analysis))
    print(f"\n✅ Token reduction: {reduction:.1f}%")
    
    print("\nCompact data preview:")
    print("-" * 70)
    print(compact[:500])
    print("...")


async def main():
    """Run all examples"""
    print("\n🎬 Statistics Generation Examples\n")
    
    # Example 1: Single component
    await example_single_component()
    
    # Example 2: All components
    await example_all_components()
    
    # Example 3: Token comparison
    await example_token_comparison()
    
    print("\n" + "=" * 70)
    print("✅ All examples completed!")
    print("=" * 70)
    print("\nNext steps:")
    print("1. Check outputs/{project_id}/statistics/ for generated files")
    print("2. Integrate with your existing video analysis pipeline")
    print("3. Customize prompts in statistics_prompts.py as needed")
    print("4. See STATISTICS_README.md for full documentation")
    print()


if __name__ == "__main__":
    asyncio.run(main())
