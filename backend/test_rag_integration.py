#!/usr/bin/env python3
"""
Test RAG integration functionality
"""

import requests
import time
import json

API_BASE_URL = "http://localhost:8000"

def wait_for_backend():
    """Wait for backend to be ready"""
    print("⏳ Waiting for backend to be ready...")
    for i in range(30):  # Wait up to 30 seconds
        try:
            response = requests.get(f"{API_BASE_URL}/docs", timeout=2)
            if response.status_code == 200:
                print("✅ Backend is ready!")
                return True
        except:
            pass
        time.sleep(1)
    print("❌ Backend failed to start")
    return False

def test_rag_endpoints():
    """Test RAG-related API endpoints"""
    print("🧪 Testing RAG endpoints...")

    # Test 1: Create a test project
    print("  Creating test project...")
    project_data = {
        "name": "RAG Test Project",
        "video_url": "https://example.com/test-video.mp4",
        "gemini_cached_content_name": "test_cached_content"
    }

    try:
        # Create user first
        response = requests.post(f"{API_BASE_URL}/api/users", json={"id": 1, "email": "test@example.com"})
        print(f"    User creation: {response.status_code}")

        # Create project
        response = requests.post(f"{API_BASE_URL}/api/projects", json=project_data)
        if response.status_code == 201:
            project = response.json()
            project_id = project["id"]
            print(f"    ✅ Project created: ID {project_id}")

            # Test 2: Check vector status endpoint
            print("  Testing vector status endpoint...")
            response = requests.get(f"{API_BASE_URL}/api/projects/{project_id}/vector-status")
            if response.status_code == 200:
                status = response.json()
                print(f"    ✅ Vector status: {status['status']}")

                # Test 3: Trigger vector generation
                print("  Testing vector generation trigger...")
                response = requests.post(f"{API_BASE_URL}/api/projects/{project_id}/generate-vector-data")
                if response.status_code == 200:
                    trigger_result = response.json()
                    print(f"    ✅ Vector generation triggered: {trigger_result['status']}")
                else:
                    print(f"    ❌ Vector generation trigger failed: {response.status_code}")
            else:
                print(f"    ❌ Vector status check failed: {response.status_code}")

            # Test 4: Test chat with project mention
            print("  Testing chat with project mention...")
            chat_data = {
                "chat_id": None,
                "message": f"@RAG Test Project What can you tell me about this video?",
                "user_id": 1
            }

            response = requests.post(f"{API_BASE_URL}/api/chats/send-message", json=chat_data)
            if response.status_code == 200:
                chat_result = response.json()
                print(f"    ✅ Chat created: ID {chat_result['chat_id']}")
                print(f"    📝 Assistant response length: {len(chat_result['messages'][-1]['content'])} chars")
            else:
                print(f"    ❌ Chat failed: {response.status_code} - {response.text}")

        else:
            print(f"    ❌ Project creation failed: {response.status_code} - {response.text}")

    except Exception as e:
        print(f"❌ Test failed with exception: {e}")

def main():
    """Run RAG integration tests"""
    print("🚀 Testing RAG Integration...")

    if not wait_for_backend():
        return 1

    test_rag_endpoints()

    print("🎉 RAG Integration testing complete!")
    return 0

if __name__ == "__main__":
    exit(main())
