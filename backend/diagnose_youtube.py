"""
Standalone YouTube Integration Diagnostic Script

This version has NO dependencies on your app code.
Just update the DATABASE_URL and run it from anywhere.
"""

import os
from datetime import datetime, timezone
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base

# ========================================
# CONFIGURATION - UPDATE THESE
# ========================================

# Update this to match your database location
DATABASE_URL = "sqlite:///D:/web_dev/v0-social/app.db"

# If your tables have different names, update these:
USER_TABLE = "users"
OAUTH_TABLE = "oauth_connections"

# ========================================

Base = declarative_base()


class User(Base):
    __tablename__ = USER_TABLE
    id = Column(Integer, primary_key=True)
    email = Column(String, nullable=True)
    name = Column(String, nullable=True)


class OAuthConnection(Base):
    __tablename__ = OAUTH_TABLE
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    provider = Column(String)
    access_token = Column(Text)
    refresh_token = Column(Text)
    expires_at = Column(DateTime)
    created_at = Column(DateTime)


# Verify database file exists
if DATABASE_URL.startswith("sqlite:///"):
    db_path = DATABASE_URL.replace("sqlite:///", "").replace("./", "")
    if not os.path.exists(db_path):
        print(f"❌ Database file not found at: {db_path}")
        print(f"   Please update DATABASE_URL in this script")
        exit(1)
    else:
        print(f"✓ Database found at: {db_path}")

# Create engine and session
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


def test_youtube_api(access_token: str, max_results: int = 5):
    """Test YouTube API directly without app dependencies"""
    import requests
    
    headers = {"Authorization": f"Bearer {access_token}"}
    base_url = "https://www.googleapis.com/youtube/v3"
    
    try:
        # Test search endpoint
        print("   Testing YouTube API search...")
        search_resp = requests.get(
            f"{base_url}/search",
            params={
                "part": "snippet",
                "forMine": "true",
                "type": "video",
                "order": "date",
                "maxResults": str(max_results),
            },
            headers=headers,
            timeout=10.0,
        )
        
        if search_resp.status_code != 200:
            print(f"   ❌ API Error: {search_resp.status_code}")
            print(f"   Response: {search_resp.text[:200]}")
            return []
        
        search_data = search_resp.json()
        video_ids = [
            item.get("id", {}).get("videoId")
            for item in search_data.get("items", [])
            if item.get("id", {}).get("videoId")
        ]
        
        if not video_ids:
            print("   ⚠️  No videos found in search results")
            print("   (Your channel might not have any uploaded videos)")
            return []
        
        print(f"   ✓ Found {len(video_ids)} video IDs")
        
        # Get video details
        print("   Fetching video details...")
        videos_resp = requests.get(
            f"{base_url}/videos",
            params={
                "part": "snippet,statistics",
                "id": ",".join(video_ids),
            },
            headers=headers,
            timeout=10.0,
        )
        
        if videos_resp.status_code != 200:
            print(f"   ❌ API Error: {videos_resp.status_code}")
            return []
        
        videos = videos_resp.json().get("items", [])
        return videos
        
    except Exception as e:
        print(f"   ❌ Exception: {type(e).__name__}: {str(e)}")
        return []


def diagnose():
    db = SessionLocal()
    
    try:
        print()
        print("=" * 70)
        print("YouTube Integration Diagnostic (Standalone Version)")
        print("=" * 70)
        print()
        
        # Check User
        user = db.query(User).filter(User.id == 1).first()
        if not user:
            print("❌ No user found with ID 1")
            print("   The database might be empty or tables not created yet")
            return
        
        print(f"✓ User found:")
        print(f"  ID: {user.id}")
        print(f"  Email: {user.email or 'Not set'}")
        print(f"  Name: {user.name or 'Not set'}")
        print()
        
        # Check OAuth connections
        connections = db.query(OAuthConnection).filter(
            OAuthConnection.user_id == user.id
        ).all()
        
        if not connections:
            print("❌ No OAuth connections found")
            print()
            print("   Next steps:")
            print("   1. Start your FastAPI server")
            print("   2. Visit: http://localhost:8000/oauth/youtube/authorize")
            print("   3. Complete the Google OAuth flow")
            print("   4. Run this script again")
            return
        
        print(f"✓ Found {len(connections)} OAuth connection(s):")
        print()
        
        youtube_conn = None
        for conn in connections:
            is_youtube = conn.provider == "youtube"
            marker = "👉 " if is_youtube else "   "
            
            print(f"{marker}Provider: {conn.provider}")
            print(f"   Access Token: {'✓ Present' if conn.access_token else '❌ Missing'}")
            print(f"   Refresh Token: {'✓ Present' if conn.refresh_token else '❌ Missing'}")
            
            if is_youtube:
                youtube_conn = conn
            
            if conn.expires_at:
                now = datetime.now(timezone.utc) if conn.expires_at.tzinfo else datetime.utcnow()
                is_expired = conn.expires_at < now
                
                if is_expired:
                    print(f"   Token Status: ❌ EXPIRED")
                    print(f"   Expired at: {conn.expires_at}")
                else:
                    time_diff = conn.expires_at - now
                    hours = time_diff.total_seconds() / 3600
                    if hours > 24:
                        time_str = f"{hours/24:.1f} days"
                    else:
                        time_str = f"{hours:.1f} hours"
                    print(f"   Token Status: ✓ Valid")
                    print(f"   Expires in: {time_str}")
            else:
                print(f"   Token Status: ⚠️  No expiration set")
            
            print(f"   Created: {conn.created_at}")
            print()
        
        if not youtube_conn:
            print("❌ No YouTube connection found")
            print("   Visit: http://localhost:8000/oauth/youtube/authorize")
            return
        
        if not youtube_conn.access_token:
            print("❌ YouTube connection exists but access token is missing")
            print("   Re-authorize: http://localhost:8000/oauth/youtube/authorize")
            return
        
        # Check token expiration
        if youtube_conn.expires_at:
            now = datetime.now(timezone.utc) if youtube_conn.expires_at.tzinfo else datetime.utcnow()
            if youtube_conn.expires_at < now:
                print("❌ YouTube access token is expired")
                print("   Re-authorize: http://localhost:8000/oauth/youtube/authorize")
                return
        
        print("✅ YouTube connection looks good!")
        print()
        print("Testing YouTube API connection...")
        print()
        
        # Test API
        videos = test_youtube_api(youtube_conn.access_token, max_results=5)
        
        if videos:
            print()
            print(f"✅ SUCCESS! API returned {len(videos)} videos")
            print()
            print("Sample videos:")
            for i, video in enumerate(videos[:3], 1):
                snippet = video.get("snippet", {})
                stats = video.get("statistics", {})
                title = snippet.get("title", "Untitled")
                channel = snippet.get("channelTitle", "Unknown")
                views = stats.get("viewCount", "N/A")
                
                print(f"  {i}. {title[:60]}")
                print(f"     Channel: {channel}")
                print(f"     Views: {views:,}" if isinstance(views, int) else f"     Views: {views}")
                print()
            
            print("=" * 70)
            print("✅ Your YouTube integration is working correctly!")
            print("=" * 70)
        else:
            print()
            print("⚠️  No videos returned")
            print()
            print("   This could mean:")
            print("   • Your channel has no uploaded videos")
            print("   • API permissions issue")
            print("   • Token needs refresh")
            print()
            print("   Check the API error messages above for details")
        
        print()
        
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {str(e)}")
        print()
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    # Check for requests library
    try:
        import requests
    except ImportError:
        print("❌ Missing 'requests' library")
        print("   Install it with: pip install requests")
        exit(1)
    
    diagnose()