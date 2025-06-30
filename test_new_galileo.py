#!/usr/bin/env python3
"""
Simple test to verify the new Galileo configuration.
"""

import os
from dotenv import load_dotenv
from agent_framework.utils.logging import GalileoLoggerWrapper

def test_new_galileo_config():
    """Test the new Galileo configuration"""
    
    # Force reload environment variables
    load_dotenv(override=True)
    
    print("🔍 Testing New Galileo Configuration")
    print("=" * 50)
    
    # Get current values
    api_key = os.getenv("GALILEO_API_KEY")
    project_id = os.getenv("GALILEO_PROJECT_ID")
    log_stream = os.getenv("GALILEO_LOG_STREAM")
    
    print(f"📋 Current Configuration:")
    print(f"   API Key: {'✅ Set' if api_key else '❌ Not Set'}")
    if api_key:
        print(f"   API Key Preview: {api_key[:10]}...{api_key[-4:]}")
    print(f"   Project ID: {project_id}")
    print(f"   Log Stream: {log_stream}")
    print()
    
    if not api_key:
        print("❌ No API key found!")
        return False
    
    # Test Galileo initialization
    print("🧪 Testing Galileo initialization...")
    try:
        galileo_logger = GalileoLoggerWrapper(project=project_id, log_stream=log_stream)
        
        if galileo_logger.is_initialized:
            print("✅ Galileo initialized successfully!")
            
            # Test trace creation
            print("🧪 Testing trace creation...")
            trace = galileo_logger.start_trace(
                input="Test input for new configuration",
                name="New Config Test",
                metadata={"test": "new_config"},
                tags=["test", "new_config"]
            )
            
            if trace:
                print("✅ Trace created successfully!")
                
                # Test LLM span
                galileo_logger.add_llm_span(
                    input="Test LLM input",
                    output="Test LLM output",
                    model="gpt-4",
                    name="Test LLM"
                )
                print("✅ LLM span added!")
                
                # Conclude and flush
                galileo_logger.conclude(output="Test completed successfully")
                galileo_logger.flush()
                print("✅ Trace concluded and flushed!")
                
                print("\n🎉 All tests passed! Galileo is working correctly.")
                return True
            else:
                print("❌ Trace creation failed!")
                return False
        else:
            print("❌ Galileo initialization failed!")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_new_galileo_config()
    if not success:
        print("\n❌ Galileo configuration still needs attention.")
        print("   Please check your API key and project ID.") 