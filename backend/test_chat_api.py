#!/usr/bin/env python3
"""
Test the chat API with project mentions
"""

import requests
import json

API_BASE = "http://localhost:8000"

def test_chat_api():
    """Test chat API with project mentions"""
    
    test_messages = [
        "@Mock recording Summarize this project",
        "@Mock recording what is this about?",
        "@Are we eggs ? .(Egg Theory) explain the theory"
    ]
    
    for message in test_messages:
        print(f"\nTesting: {message}")
        
        payload = {
            "chat_id": None,
            "message": message,
            "user_id": None
        }
        
        try:
            response = requests.post(
                f"{API_BASE}/api/chats/send-message",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✓ Success!")
                print(f"  Project: {result['project']['name']}")
                print(f"  RAG Active: {result['rag_active']}")
                print(f"  Context Chunks Used: {result['context_chunks_used']}")
                print(f"  Messages: {len(result['messages'])}")
            else:
                print(f"✗ Error {response.status_code}: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"✗ Request failed: {e}")

if __name__ == '__main__':
    test_chat_api()
