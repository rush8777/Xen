I need to create a backend system that lists cross-platform videos for the create-project component. Here's what I found:

## Current State Analysis

**Frontend Component ([create-project.tsx](cci:7://file:///d:/web_dev/v0-social/components/xen/create-project.tsx:0:0-0:0)):**
- Shows a video grid with hardcoded sample data
- Has filter controls for categories, sorting, and filters
- Displays video metadata (title, channel, views, duration, stats)
- Needs to connect to a real backend API

**Backend Infrastructure:**
- Main FastAPI app with OAuth connections for YouTube, Facebook, Instagram, Twitter, TikTok
- Existing yt-dlp service for downloading videos
- Database models for users and OAuth connections
- Missing: Video listing/aggregation functionality

## Proposed Backend Architecture

I'll create a comprehensive video library system that:

1. **Video Library Router** - New API endpoints for video discovery
2. **Video Models** - Database models to store video metadata
3. **Platform Integrations** - Use existing OAuth connections to fetch videos
4. **Cross-platform Aggregation** - Combine videos from all connected platforms
5. **Search & Filtering** - Support the frontend's filter requirements

## Implementation Plan

### 1. Database Models
- Video table to store aggregated video metadata
- PlatformVideo table for platform-specific data
- Support for caching and periodic updates

### 2. API Endpoints
- GET /api/videos - List videos with filtering/sorting
- GET /api/videos/{video_id} - Get video details
- POST /api/videos/refresh - Refresh video library from platforms
- GET /api/videos/categories - Get available categories

### 3. Platform Services
- YouTube API integration (using existing OAuth)
- Facebook/Instagram Graph API
- TikTok API
- Twitter API

### 4. Integration Points
- Connect to existing OAuth system
- Leverage yt-dlp for video info when needed
- Provide the exact data structure the frontend expects

Would you like me to proceed with implementing this backend system? I'll need to switch to Code mode to create the files and make the necessary modifications.

The implementation will include:
- New database models for videos
- Platform-specific service classes
- Video library router with full CRUD operations
- Integration with existing OAuth connections
- API endpoints that match the frontend's expected data format