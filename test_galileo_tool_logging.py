#!/usr/bin/env python3
"""
Test script to verify Galileo tool logging with individual spans.
This script tests both silly and serious modes to ensure each tool is properly logged.
"""

import asyncio
import json
from dotenv import load_dotenv
from agent import SimpleAgent

# Load environment variables
load_dotenv()

async def test_silly_mode():
    """Test silly mode with proper tool logging"""
    print("🎭 Testing Silly Mode with Galileo Tool Logging")
    print("=" * 60)
    
    # Create agent in silly mode
    agent = SimpleAgent(mode="silly")
    
    # Test parameters
    task = "Generate a creative startup pitch"
    industry = "tech"
    audience = "millennials"
    random_word = "pizza"
    
    print(f"Task: {task}")
    print(f"Industry: {industry}")
    print(f"Audience: {audience}")
    print(f"Random Word: {random_word}")
    print()
    
    try:
        # Execute the agent
        result = await agent.run(task, industry, audience, random_word)
        
        # Parse the result
        if isinstance(result, str):
            try:
                parsed_result = json.loads(result)
                final_output = parsed_result.get("final_output", result)
            except json.JSONDecodeError:
                final_output = result
        else:
            final_output = result
        
        print("✅ Silly Mode Test Completed Successfully!")
        print(f"Final Output: {final_output}")
        print()
        
        return True
        
    except Exception as e:
        print(f"❌ Silly Mode Test Failed: {e}")
        return False

async def test_serious_mode():
    """Test serious mode with proper tool logging"""
    print("📊 Testing Serious Mode with Galileo Tool Logging")
    print("=" * 60)
    
    # Create agent in serious mode
    agent = SimpleAgent(mode="serious")
    
    # Test parameters
    task = "Generate a professional startup business plan"
    industry = "fintech"
    audience = "enterprise"
    random_word = "blockchain"
    
    print(f"Task: {task}")
    print(f"Industry: {industry}")
    print(f"Audience: {audience}")
    print(f"Random Word: {random_word}")
    print()
    
    try:
        # Execute the agent
        result = await agent.run(task, industry, audience, random_word)
        
        # Parse the result
        if isinstance(result, str):
            try:
                parsed_result = json.loads(result)
                final_output = parsed_result.get("final_output", result)
            except json.JSONDecodeError:
                final_output = result
        else:
            final_output = result
        
        print("✅ Serious Mode Test Completed Successfully!")
        print(f"Final Output: {final_output}")
        print()
        
        return True
        
    except Exception as e:
        print(f"❌ Serious Mode Test Failed: {e}")
        return False

async def main():
    """Run all tests"""
    print("🔍 Galileo Tool Logging Test Suite")
    print("=" * 60)
    print("This test verifies that each tool is properly logged as an individual span in Galileo.")
    print("Check your Galileo dashboard to see the tool spans and traces.")
    print()
    
    # Test silly mode
    silly_success = await test_silly_mode()
    
    print("-" * 60)
    
    # Test serious mode
    serious_success = await test_serious_mode()
    
    print("=" * 60)
    print("📊 Test Results Summary")
    print("=" * 60)
    print(f"Silly Mode: {'✅ PASSED' if silly_success else '❌ FAILED'}")
    print(f"Serious Mode: {'✅ PASSED' if serious_success else '❌ FAILED'}")
    
    if silly_success and serious_success:
        print("\n🎉 All tests passed! Check your Galileo dashboard for:")
        print("   • Individual tool spans for each tool execution")
        print("   • Proper trace hierarchy showing tool relationships")
        print("   • Input/output logging for each tool")
        print("   • Error handling and fallback mechanisms")
    else:
        print("\n⚠️  Some tests failed. Check the error messages above.")
    
    print("\n📋 Expected Galileo Spans:")
    print("   • Agent Workflow (main trace)")
    print("   • execute_hackernews_tool (silly mode)")
    print("   • execute_startup_simulator (silly mode)")
    print("   • execute_news_api_tool (serious mode)")
    print("   • execute_serious_startup_simulator (serious mode)")
    print("   • format_result (result formatting)")

if __name__ == "__main__":
    asyncio.run(main()) 