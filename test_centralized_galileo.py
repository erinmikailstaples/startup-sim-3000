#!/usr/bin/env python3
"""
Test centralized Galileo logging across all components.
"""

import os
from dotenv import load_dotenv
from agent_framework.utils.logging import get_galileo_logger
from tools.startup_simulator import StartupSimulatorTool
from tools.serious_startup_simulator import SeriousStartupSimulatorTool

def test_centralized_galileo():
    """Test centralized Galileo logging"""
    
    # Load environment variables
    load_dotenv()
    
    print("🔍 Testing Centralized Galileo Logging")
    print("=" * 50)
    
    # Test 1: Get centralized logger
    print("🧪 Test 1: Centralized Logger Initialization")
    galileo_logger = get_galileo_logger()
    
    if galileo_logger and galileo_logger.is_initialized:
        print("✅ Centralized logger initialized successfully!")
        print(f"   Project: {galileo_logger.project}")
        print(f"   Log Stream: {galileo_logger.log_stream}")
    else:
        print("❌ Centralized logger failed to initialize!")
        return False
    
    # Test 2: Test trace creation
    print("\n🧪 Test 2: Trace Creation")
    trace = galileo_logger.start_trace(
        input="Test centralized logging",
        name="Centralized Test",
        metadata={"test": "centralized"},
        tags=["test", "centralized"]
    )
    
    if trace:
        print("✅ Trace created successfully!")
        
        # Test LLM span
        galileo_logger.add_llm_span(
            input="Test input",
            output="Test output",
            model="gpt-4",
            name="Test LLM"
        )
        print("✅ LLM span added!")
        
        # Conclude and flush
        galileo_logger.conclude(output="Centralized test completed")
        galileo_logger.flush()
        print("✅ Trace concluded and flushed!")
    else:
        print("❌ Trace creation failed!")
        return False
    
    # Test 3: Test tool initialization
    print("\n🧪 Test 3: Tool Initialization")
    try:
        startup_tool = StartupSimulatorTool()
        serious_tool = SeriousStartupSimulatorTool()
        
        if startup_tool.galileo_logger and startup_tool.galileo_logger.is_initialized:
            print("✅ Startup simulator tool logger initialized!")
        else:
            print("❌ Startup simulator tool logger failed!")
            return False
            
        if serious_tool.galileo_logger and serious_tool.galileo_logger.is_initialized:
            print("✅ Serious simulator tool logger initialized!")
        else:
            print("❌ Serious simulator tool logger failed!")
            return False
            
    except Exception as e:
        print(f"❌ Tool initialization error: {e}")
        return False
    
    print("\n🎉 All centralized Galileo tests passed!")
    return True

if __name__ == "__main__":
    success = test_centralized_galileo()
    if success:
        print("\n✅ Centralized Galileo logging is working correctly!")
        print("   All components will now use the same Galileo instance.")
    else:
        print("\n❌ Centralized Galileo logging needs attention.") 