#!/usr/bin/env python3
"""
🧪 TEST SCRIPT: Demonstrating Galileo Usage with Explicit Comments

This script shows exactly where and how Galileo is used throughout the application.
It's designed to help new developers understand the observability flow.

Key Galileo Usage Points:
1. 🔍 Galileo is DEFINED in agent_framework/utils/logging.py
2. 👀 Galileo is INITIALIZED in each tool's __init__ method
3. 🚀 Galileo TRACES are started in each tool's execute method
4. 📊 Galileo SPANS are added for LLM calls and tool execution
5. ✅ Galileo TRACES are concluded when tools complete
6. ❌ Galileo ERROR handling when tools fail
"""

import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_galileo_usage():
    """Test all tools to demonstrate Galileo usage"""
    
    print("🧪 STARTING GALILEO USAGE DEMONSTRATION")
    print("=" * 60)
    
    # 👀 GALILEO DEFINITION POINT 1: Import the centralized logger
    # This is where Galileo is defined - in the logging utility
    from agent_framework.utils.logging import get_galileo_logger
    
    print("\n🔍 GALILEO DEFINITION:")
    print("   Galileo is defined in: agent_framework/utils/logging.py")
    print("   Function: get_galileo_logger()")
    print("   This creates a centralized GalileoLogger instance")
    
    # 👀 GALILEO INITIALIZATION POINT 2: Get the logger instance
    # This is where Galileo is initialized for use
    galileo_logger = get_galileo_logger()
    
    if galileo_logger:
        print("\n✅ GALILEO INITIALIZATION SUCCESSFUL:")
        print("   - API Key: Found in environment")
        print("   - Project: Using GALILEO_PROJECT from .env")
        print("   - Log Stream: Using GALILEO_LOG_STREAM from .env")
    else:
        print("\n⚠️  GALILEO INITIALIZATION FAILED:")
        print("   - Check GALILEO_API_KEY in .env file")
        print("   - Check GALILEO_PROJECT in .env file")
        return
    
    print("\n👀 GALILEO USAGE IN TOOLS:")
    print("   Each tool follows this pattern:")
    print("   1. Import get_galileo_logger in __init__")
    print("   2. Start trace in execute() method")
    print("   3. Add spans for LLM calls")
    print("   4. Conclude trace with success/error")
    
    # Test each tool to show Galileo usage
    tools_to_test = [
        ("HackerNews Tool", "tools.hackernews_tool", "HackerNewsTool"),
        ("News API Tool", "tools.news_api_tool", "NewsAPITool"),
        ("Startup Simulator", "tools.startup_simulator", "StartupSimulatorTool"),
        ("Serious Startup Simulator", "tools.serious_startup_simulator", "SeriousStartupSimulatorTool")
    ]
    
    for tool_name, module_path, class_name in tools_to_test:
        print(f"\n🔧 TESTING {tool_name}:")
        print(f"   Module: {module_path}")
        print(f"   Class: {class_name}")
        
        try:
            # Import the tool module
            module = __import__(module_path, fromlist=[class_name])
            tool_class = getattr(module, class_name)
            
            # 👀 GALILEO INITIALIZATION POINT 3: Tool initialization
            # This is where each tool gets its Galileo logger
            tool = tool_class()
            
            print(f"   ✅ Tool initialized successfully")
            print(f"   👀 Galileo logger: {'Available' if tool.galileo_logger else 'Not available'}")
            
            # Test tool execution (this will create Galileo traces)
            if tool_name == "HackerNews Tool":
                result = await tool.execute(limit=2)
            elif tool_name == "News API Tool":
                result = await tool.execute(category="business", limit=2)
            elif tool_name == "Startup Simulator":
                result = await tool.execute(
                    industry="Tech", 
                    audience="Developers", 
                    random_word="AI"
                )
            elif tool_name == "Serious Startup Simulator":
                result = await tool.execute(
                    industry="Finance", 
                    audience="Investors", 
                    random_word="blockchain"
                )
            
            print(f"   ✅ Tool execution completed")
            print(f"   📊 Galileo trace created in dashboard")
            
        except Exception as e:
            print(f"   ❌ Tool test failed: {e}")
    
    print("\n🎯 GALILEO DASHBOARD CHECK:")
    print("   After running this test, check your Galileo dashboard for:")
    print("   - 4 individual tool traces (one per tool)")
    print("   - LLM spans within each trace")
    print("   - Input/output data for each tool")
    print("   - Execution timing and performance metrics")
    
    print("\n📚 EDUCATIONAL SUMMARY:")
    print("   Galileo is used in these key places:")
    print("   1. 🔍 DEFINITION: agent_framework/utils/logging.py")
    print("   2. 👀 INITIALIZATION: Each tool's __init__ method")
    print("   3. 🚀 TRACE START: Each tool's execute() method")
    print("   4. 📊 SPAN ADDITION: Before and after LLM calls")
    print("   5. ✅ TRACE CONCLUSION: End of execute() method")
    print("   6. ❌ ERROR HANDLING: Exception blocks")
    
    print("\n🎉 GALILEO USAGE DEMONSTRATION COMPLETE!")

if __name__ == "__main__":
    # Check environment variables
    print("🔧 ENVIRONMENT CHECK:")
    print(f"   GALILEO_API_KEY: {'✅ Set' if os.getenv('GALILEO_API_KEY') else '❌ Not set'}")
    print(f"   GALILEO_PROJECT: {'✅ Set' if os.getenv('GALILEO_PROJECT') else '❌ Not set'}")
    print(f"   GALILEO_LOG_STREAM: {'✅ Set' if os.getenv('GALILEO_LOG_STREAM') else '❌ Not set'}")
    
    # Run the test
    asyncio.run(test_galileo_usage()) 