#!/usr/bin/env python3
"""
Test modern Galileo setup with context manager and direct GalileoLogger usage.
"""

import os
from dotenv import load_dotenv
from galileo import galileo_context, GalileoLogger
from agent_framework.utils.logging import get_galileo_logger

def test_modern_galileo_setup():
    """Test modern Galileo setup"""
    
    # Load environment variables
    load_dotenv()
    
    print("🔍 Testing Modern Galileo Setup")
    print("=" * 50)
    
    # Check environment variables
    api_key = os.getenv("GALILEO_API_KEY")
    project = os.getenv("GALILEO_PROJECT")
    log_stream = os.getenv("GALILEO_LOG_STREAM")
    
    print(f"📋 Environment Variables:")
    print(f"   GALILEO_API_KEY: {'✅ Set' if api_key else '❌ Not Set'}")
    if api_key:
        print(f"   API Key Preview: {api_key[:10]}...{api_key[-4:]}")
    print(f"   GALILEO_PROJECT: {project or '❌ Not Set'}")
    print(f"   GALILEO_LOG_STREAM: {log_stream or '❌ Not Set'}")
    print()
    
    if not api_key:
        print("❌ GALILEO_API_KEY not set. Cannot proceed with testing.")
        return False
    
    # Test 1: Direct GalileoLogger initialization
    print("🧪 Test 1: Direct GalileoLogger Initialization")
    try:
        logger = GalileoLogger()  # Should use env vars automatically
        print("✅ GalileoLogger initialized successfully!")
    except Exception as e:
        print(f"❌ GalileoLogger initialization failed: {e}")
        return False
    
    # Test 2: Centralized logger
    print("\n🧪 Test 2: Centralized Logger")
    centralized_logger = get_galileo_logger()
    if centralized_logger:
        print("✅ Centralized logger initialized successfully!")
    else:
        print("❌ Centralized logger failed!")
        return False
    
    # Test 3: Context manager
    print("\n🧪 Test 3: Context Manager")
    try:
        with galileo_context():
            print("✅ Context manager works!")
            # Simulate some work
            print("   Simulating agent work...")
    except Exception as e:
        print(f"❌ Context manager failed: {e}")
        return False
    
    print("\n🎉 All modern Galileo tests passed!")
    return True

if __name__ == "__main__":
    success = test_modern_galileo_setup()
    if success:
        print("\n✅ Modern Galileo setup is working correctly!")
        print("   Your Flask app should now log traces properly.")
    else:
        print("\n❌ Modern Galileo setup needs attention.")
        print("   Please check your environment variables and Galileo credentials.") 