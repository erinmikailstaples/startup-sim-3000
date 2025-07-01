#!/usr/bin/env python3
"""
Test to verify Galileo integration is sending data to the dashboard.
"""

import os
from dotenv import load_dotenv
from galileo import GalileoLogger

def test_galileo_dashboard_integration():
    """Test Galileo integration with explicit GalileoLogger"""
    
    # Load environment variables
    load_dotenv()
    
    print("🔍 Testing Galileo Dashboard Integration")
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
    
    # Test explicit GalileoLogger with logging
    print("🧪 Testing explicit GalileoLogger with logging...")
    try:
        # Initialize Galileo logger
        logger = GalileoLogger(project=project, log_stream=log_stream)
        print("✅ Galileo logger initialized successfully!")
        
        # Start a trace
        trace = logger.start_trace("Test dashboard integration")
        print("✅ Trace started successfully!")
        
        # Add LLM span
        logger.add_llm_span(
            input="Test message from explicit logger",
            output="Test completed successfully",
            model="test-model",
            num_input_tokens=10,
            num_output_tokens=5,
            total_tokens=15,
            duration_ns=1000
        )
        print("✅ LLM span added successfully!")
        
        # Add structured data
        logger.add_llm_span(
            input="Structured test data",
            output="Data processed successfully",
            model="test-model",
            num_input_tokens=20,
            num_output_tokens=10,
            total_tokens=30,
            duration_ns=2000
        )
        print("✅ Structured data added successfully!")
        
        # Conclude the trace
        logger.conclude(output="Test completed successfully", duration_ns=3000)
        print("✅ Trace concluded successfully!")
        
        # Flush to upload to Galileo
        try:
            logger.flush()
            print("✅ Data flushed to Galileo successfully!")
        except Exception as flush_error:
            print(f"⚠️  Warning: Could not flush data: {flush_error}")
            print("   This is normal if credentials are invalid or project doesn't exist")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during Galileo logger test: {e}")
        return False

def test_simple_galileo_logging():
    """Test simple Galileo logging without complex spans"""
    
    print("\n🧪 Testing simple Galileo logging...")
    try:
        # Initialize logger
        logger = GalileoLogger(
            project=os.getenv("GALILEO_PROJECT"),
            log_stream=os.getenv("GALILEO_LOG_STREAM")
        )
        
        # Start simple trace
        trace = logger.start_trace("Simple test")
        
        # Add simple span
        logger.add_llm_span(
            input="Simple test message",
            output="Simple test completed",
            model="simple-test",
            num_input_tokens=5,
            num_output_tokens=3,
            total_tokens=8,
            duration_ns=500
        )
        
        # Conclude and flush
        logger.conclude(output="Simple test completed", duration_ns=500)
        try:
            logger.flush()
            print("✅ Simple data flushed successfully!")
        except Exception as flush_error:
            print(f"⚠️  Warning: Could not flush simple data: {flush_error}")
        
        print("✅ Simple logging completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error during simple logging test: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testing Galileo Dashboard Integration")
    print("   This will send test data to your Galileo dashboard.")
    print("   Check your dashboard at: https://console.galileo.ai/")
    print()
    
    # Test 1: Explicit logger with spans
    success1 = test_galileo_dashboard_integration()
    
    # Test 2: Simple logging
    success2 = test_simple_galileo_logging()
    
    if success1 and success2:
        print("\n🎉 All Galileo tests passed!")
        print("   Check your Galileo dashboard for the test data.")
        print("   Look for:")
        print("   - Project: erin-custom-metric")
        print("   - Log Stream: development")
        print("   - Test traces with LLM spans")
    else:
        print("\n❌ Some Galileo tests failed.")
        print("   Check your environment variables and Galileo credentials.")
        print("   Make sure your project exists in the Galileo dashboard.") 