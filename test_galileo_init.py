#!/usr/bin/env python3
"""
Test script to verify Galileo initialization is working correctly.
This script will test the Galileo configuration and show what values are being used.
"""

import os
from dotenv import load_dotenv
from agent_framework.utils.logging import GalileoLoggerWrapper

def test_galileo_initialization():
    """Test Galileo initialization with current environment variables"""
    
    # Load environment variables
    load_dotenv()
    
    print("🔍 Testing Galileo Initialization...")
    print("=" * 50)
    
    # Check environment variables
    api_key = os.getenv("GALILEO_API_KEY")
    project_id = os.getenv("GALILEO_PROJECT_ID")
    log_stream = os.getenv("GALILEO_LOG_STREAM")
    
    print(f"📋 Environment Variables:")
    print(f"   GALILEO_API_KEY: {'✅ Set' if api_key else '❌ Not Set'}")
    print(f"   GALILEO_PROJECT_ID: {project_id or '❌ Not Set'}")
    print(f"   GALILEO_LOG_STREAM: {log_stream or '❌ Not Set'}")
    print()
    
    if not api_key:
        print("⚠️  Warning: GALILEO_API_KEY not set. Galileo logging will be disabled.")
        return False
    
    # Test GalileoLoggerWrapper initialization
    print("🧪 Testing GalileoLoggerWrapper...")
    try:
        galileo_logger = GalileoLoggerWrapper(project=project_id, log_stream=log_stream)
        
        if galileo_logger.is_initialized:
            print("✅ GalileoLoggerWrapper initialized successfully!")
            print(f"   Project: {galileo_logger.project}")
            print(f"   Log Stream: {galileo_logger.log_stream}")
            
            # Test trace creation
            print("\n🧪 Testing trace creation...")
            trace = galileo_logger.start_trace(
                input="Test input",
                name="Test Trace",
                metadata={"test": "true"},
                tags=["test"]
            )
            
            if trace:
                print("✅ Trace created successfully!")
                
                # Test LLM span
                print("🧪 Testing LLM span...")
                galileo_logger.add_llm_span(
                    input="Test LLM input",
                    output="Test LLM output",
                    model="gpt-4",
                    name="Test LLM"
                )
                print("✅ LLM span added successfully!")
                
                # Test trace conclusion
                print("🧪 Testing trace conclusion...")
                galileo_logger.conclude(output="Test output")
                print("✅ Trace concluded successfully!")
                
                # Test flush
                print("🧪 Testing flush...")
                galileo_logger.flush()
                print("✅ Flush completed successfully!")
                
            else:
                print("❌ Trace creation failed!")
                return False
                
        else:
            print("❌ GalileoLoggerWrapper initialization failed!")
            return False
            
    except Exception as e:
        print(f"❌ Error during Galileo testing: {e}")
        return False
    
    print("\n🎉 All Galileo tests passed!")
    return True

if __name__ == "__main__":
    success = test_galileo_initialization()
    if success:
        print("\n✅ Galileo is properly configured and ready to use!")
    else:
        print("\n❌ Galileo configuration needs attention.")
        print("   Please check your .env file and Galileo API credentials.") 