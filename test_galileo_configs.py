#!/usr/bin/env python3
"""
Comprehensive test script to verify Galileo configuration with environment variables.
This will test different project configurations and show exactly what's being used.
"""

import os
from dotenv import load_dotenv
from agent_framework.utils.logging import GalileoLoggerWrapper

def test_galileo_configurations():
    """Test Galileo with different configurations"""
    
    # Load environment variables
    load_dotenv()
    
    print("🔍 Comprehensive Galileo Configuration Test")
    print("=" * 60)
    
    # Get all environment variables
    api_key = os.getenv("GALILEO_API_KEY")
    project_id = os.getenv("GALILEO_PROJECT_ID")
    log_stream = os.getenv("GALILEO_LOG_STREAM")
    
    print(f"📋 Current Environment Variables:")
    print(f"   GALILEO_API_KEY: {'✅ Set' if api_key else '❌ Not Set'}")
    if api_key:
        print(f"   API Key Preview: {api_key[:10]}...{api_key[-4:]}")
    print(f"   GALILEO_PROJECT_ID: {project_id or '❌ Not Set'}")
    print(f"   GALILEO_LOG_STREAM: {log_stream or '❌ Not Set'}")
    print()
    
    if not api_key:
        print("❌ GALILEO_API_KEY not set. Cannot proceed with testing.")
        return False
    
    # Test configurations to try
    test_configs = [
        {
            "name": "Current .env configuration",
            "project": project_id,
            "log_stream": log_stream
        },
        {
            "name": "Example configuration (startup-simulator-v1.2)",
            "project": "startup-simulator-v1.2",
            "log_stream": "my_log_stream"
        },
        {
            "name": "Simple configuration (startup-sim)",
            "project": "startup-sim",
            "log_stream": "development"
        }
    ]
    
    success_count = 0
    
    for config in test_configs:
        print(f"🧪 Testing: {config['name']}")
        print(f"   Project: {config['project']}")
        print(f"   Log Stream: {config['log_stream']}")
        
        try:
            galileo_logger = GalileoLoggerWrapper(
                project=config['project'], 
                log_stream=config['log_stream']
            )
            
            if galileo_logger.is_initialized:
                print("   ✅ Initialization: SUCCESS")
                
                # Test basic functionality
                trace = galileo_logger.start_trace(
                    input="Test input",
                    name="Configuration Test",
                    metadata={"config": config['name']},
                    tags=["test", "config"]
                )
                
                if trace:
                    print("   ✅ Trace Creation: SUCCESS")
                    galileo_logger.conclude(output="Test completed successfully")
                    galileo_logger.flush()
                    print("   ✅ Full Workflow: SUCCESS")
                    success_count += 1
                else:
                    print("   ❌ Trace Creation: FAILED")
            else:
                print("   ❌ Initialization: FAILED")
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)[:100]}...")
        
        print()
    
    print(f"📊 Results: {success_count}/{len(test_configs)} configurations worked")
    
    if success_count > 0:
        print("✅ At least one configuration is working!")
        return True
    else:
        print("❌ No configurations worked. Please check your Galileo credentials.")
        return False

def show_recommended_fixes():
    """Show recommended fixes for common Galileo issues"""
    
    print("\n🔧 Recommended Fixes:")
    print("=" * 40)
    
    print("1. **Check Galileo API Key**:")
    print("   - Go to https://console.galileo.ai/")
    print("   - Verify your API key is correct")
    print("   - Make sure it has the right permissions")
    
    print("\n2. **Create Project in Galileo**:")
    print("   - Log into Galileo console")
    print("   - Create a new project with ID: 'startup-sim-tutorial'")
    print("   - Or use an existing project ID")
    
    print("\n3. **Update .env file**:")
    print("   GALILEO_API_KEY=your-actual-api-key")
    print("   GALILEO_PROJECT_ID=your-project-id")
    print("   GALILEO_LOG_STREAM=your-log-stream")
    
    print("\n4. **Test with Galileo CLI** (if available):")
    print("   galileo auth")
    print("   galileo projects list")

if __name__ == "__main__":
    success = test_galileo_configurations()
    
    if not success:
        show_recommended_fixes()
    else:
        print("\n🎉 Galileo is properly configured!")
        print("   Your application should now work with Galileo observability.") 