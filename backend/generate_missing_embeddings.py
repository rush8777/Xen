#!/usr/bin/env python3
"""
Generate embeddings for existing video sub intervals that don't have them
"""

import asyncio
import json
import logging
import sqlite3
import sys
from pathlib import Path

# Add parent directory to path to import config
sys.path.insert(0, '.')
from config import settings

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_EMBED_CLIENT = None


def _get_embed_client():
    global _EMBED_CLIENT
    if _EMBED_CLIENT is not None:
        return _EMBED_CLIENT

    from google import genai
    from gemini_backend.config import GEMINI_API_KEY

    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is not set (check backend/.env)")

    _EMBED_CLIENT = genai.Client(api_key=GEMINI_API_KEY)
    return _EMBED_CLIENT


def _build_sub_interval_text(fields: dict) -> str:
    parts = []
    for label, key in [
        ("Camera", "camera_frame"),
        ("Environment", "environment_background"),
        ("People", "people_figures"),
        ("Objects", "objects_props"),
        ("Text/Symbols", "text_symbols"),
        ("Motion", "motion_changes"),
        ("Lighting", "lighting_color"),
        ("Audio cues", "audio_visible_indicators"),
        ("Occlusions", "occlusions_limits"),
    ]:
        val = (fields.get(key) or "").strip()
        if val:
            parts.append(f"{label}: {val}")
    return "\n".join(parts).strip()


def _is_blank(s: object) -> bool:
    return s is None or (isinstance(s, str) and s.strip() == "")


def get_db_path():
    """Get database path from settings"""
    DB_PATH = settings.DATABASE_URL
    if DB_PATH.startswith('sqlite:///'):
        db_file = DB_PATH.replace('sqlite:///', '')
        if db_file.startswith('./'):
            backend_dir = Path('.').resolve()
            db_path = backend_dir / db_file[2:]
        else:
            db_path = Path(db_file).resolve()
        return db_path
    else:
        print('Only SQLite databases are supported')
        sys.exit(1)

async def generate_embedding_for_text(text: str) -> list[float] | None:
    """Generate embedding using Gemini embedding API"""
    try:
        client = _get_embed_client()
        result = client.models.embed_content(
            model="gemini-embedding-001",
            contents=text,
        )
        
        if result.embeddings and len(result.embeddings) > 0:
            return list(result.embeddings[0].values)
        return None
    except Exception as e:
        logger.error(f"Failed to generate embedding: {e}")
        return None

async def generate_embeddings_for_sub_intervals():
    """Generate embeddings for video sub intervals that don't have them"""
    db_path = get_db_path()
    
    if not db_path.exists():
        print(f'Database file not found at {db_path}')
        return
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Get sub intervals without embeddings in the new embeddings table
    cursor.execute('''
        SELECT
            vsi.id,
            vsi.raw_combined_text,
            vsi.camera_frame,
            vsi.environment_background,
            vsi.people_figures,
            vsi.objects_props,
            vsi.text_symbols,
            vsi.motion_changes,
            vsi.lighting_color,
            vsi.audio_visible_indicators,
            vsi.occlusions_limits
        FROM video_sub_intervals vsi
        LEFT JOIN sub_video_interval_embeddings svie
            ON svie.sub_interval_id = vsi.id
        WHERE svie.sub_interval_id IS NULL
    ''')
    
    rows = cursor.fetchall()
    
    if not rows:
        print("No sub intervals found that need embeddings")
        return
    
    print(f"Found {len(rows)} sub intervals that need embeddings")
    
    for i, row in enumerate(rows, 1):
        (
            row_id,
            raw_combined_text,
            camera_frame,
            environment_background,
            people_figures,
            objects_props,
            text_symbols,
            motion_changes,
            lighting_color,
            audio_visible_indicators,
            occlusions_limits,
        ) = row

        print(f"Processing {i}/{len(rows)}: ID {row_id}")

        text = raw_combined_text
        if _is_blank(text):
            text = _build_sub_interval_text(
                {
                    "camera_frame": camera_frame,
                    "environment_background": environment_background,
                    "people_figures": people_figures,
                    "objects_props": objects_props,
                    "text_symbols": text_symbols,
                    "motion_changes": motion_changes,
                    "lighting_color": lighting_color,
                    "audio_visible_indicators": audio_visible_indicators,
                    "occlusions_limits": occlusions_limits,
                }
            )

            if not _is_blank(text):
                cursor.execute(
                    '''
                        UPDATE video_sub_intervals
                        SET raw_combined_text = ?
                        WHERE id = ?
                    ''',
                    (text, row_id),
                )
        
        # Generate embedding
        embedding = await generate_embedding_for_text(text) if not _is_blank(text) else None
        
        if embedding:
            # Store embedding as JSON string
            embedding_json = json.dumps(embedding)
            
            # Insert embedding into dedicated table
            cursor.execute('''
                INSERT OR REPLACE INTO sub_video_interval_embeddings
                    (sub_interval_id, embedding)
                VALUES (?, ?)
            ''', (row_id, embedding_json))
            
            print(f"  OK: Generated embedding with {len(embedding)} dimensions")
        else:
            print("  ERROR: Failed to generate embedding")
        
        # Commit every 5 records to avoid long transactions
        if i % 5 == 0:
            conn.commit()
            print(f"  Committed {i} records")
    
    # Final commit
    conn.commit()
    conn.close()
    print(f"Completed embedding generation for {len(rows)} records")

async def generate_embeddings_for_intervals():
    """Generate embeddings for interval embeddings that don't have them"""
    db_path = get_db_path()
    
    if not db_path.exists():
        print(f'Database file not found at {db_path}')
        return
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Get intervals without embeddings
    cursor.execute('''
        SELECT ie.id, ie.interval_id, ie.combined_interval_text
        FROM interval_embeddings ie
        JOIN video_intervals vi ON ie.interval_id = vi.id
        WHERE ie.embedding IS NULL OR ie.embedding = ''
    ''')
    
    rows = cursor.fetchall()
    
    if not rows:
        print("No interval embeddings found that need embeddings")
        return
    
    print(f"Found {len(rows)} interval embeddings that need embeddings")
    
    for i, (row_id, interval_id, combined_interval_text) in enumerate(rows, 1):
        print(f"Processing {i}/{len(rows)}: ID {row_id}")

        text = combined_interval_text
        if _is_blank(text):
            cursor.execute(
                '''
                    SELECT raw_combined_text,
                           camera_frame,
                           environment_background,
                           people_figures,
                           objects_props,
                           text_symbols,
                           motion_changes,
                           lighting_color,
                           audio_visible_indicators,
                           occlusions_limits
                    FROM video_sub_intervals
                    WHERE interval_id = ?
                    ORDER BY start_time_seconds ASC
                ''',
                (interval_id,),
            )
            subs = cursor.fetchall()
            sub_texts = []
            for (
                raw_combined_text,
                camera_frame,
                environment_background,
                people_figures,
                objects_props,
                text_symbols,
                motion_changes,
                lighting_color,
                audio_visible_indicators,
                occlusions_limits,
            ) in subs:
                st = raw_combined_text
                if _is_blank(st):
                    st = _build_sub_interval_text(
                        {
                            "camera_frame": camera_frame,
                            "environment_background": environment_background,
                            "people_figures": people_figures,
                            "objects_props": objects_props,
                            "text_symbols": text_symbols,
                            "motion_changes": motion_changes,
                            "lighting_color": lighting_color,
                            "audio_visible_indicators": audio_visible_indicators,
                            "occlusions_limits": occlusions_limits,
                        }
                    )
                if not _is_blank(st):
                    sub_texts.append(st.strip())

            text = "\n\n".join(sub_texts).strip()
            if not _is_blank(text):
                cursor.execute(
                    '''
                        UPDATE interval_embeddings
                        SET combined_interval_text = ?
                        WHERE id = ?
                    ''',
                    (text, row_id),
                )
        
        # Generate embedding
        embedding = await generate_embedding_for_text(text) if not _is_blank(text) else None
        
        if embedding:
            # Store embedding as JSON string
            embedding_json = json.dumps(embedding)
            
            # Update database
            cursor.execute('''
                UPDATE interval_embeddings 
                SET embedding = ? 
                WHERE id = ?
            ''', (embedding_json, row_id))
            
            print(f"  OK: Generated embedding with {len(embedding)} dimensions")
        else:
            print("  ERROR: Failed to generate embedding")
        
        # Commit every 5 records
        if i % 5 == 0:
            conn.commit()
            print(f"  Committed {i} records")
    
    # Final commit
    conn.commit()
    conn.close()
    print(f"Completed interval embedding generation for {len(rows)} records")

async def main():
    """Main function"""
    print("=== Generating Missing Embeddings ===")
    
    # Generate embeddings for sub intervals
    await generate_embeddings_for_sub_intervals()
    
    # Generate embeddings for intervals
    await generate_embeddings_for_intervals()
    
    print("=== Embedding Generation Complete ===")

if __name__ == '__main__':
    asyncio.run(main())
