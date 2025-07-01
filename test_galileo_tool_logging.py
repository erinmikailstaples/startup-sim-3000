#!/usr/bin/env python3
"""
Test script to verify Galileo logging for all tools and agent workflow.
This script tests both silly and serious modes to ensure proper span logging.
"""

import asyncio
import os
import json
from dotenv import load_dotenv
from agent import SimpleAgent
from agent_framework.llm.openai_provider import OpenAIProvider
from agent_framework.llm.models import LLMConfig
from agent_framework.utils.logging import ConsoleAgentLogger

# Load environment variables
load_dotenv()

async def test_galileo_logging():
    """Test Galileo logging for all tools and agent workflow"""
    
    print("🧪 Testing Galileo Logging for Agent Workflow")
    print("=" * 60)
    
    # Verify environment variables
    required_vars = ["OPENAI_API_KEY", "GALILEO_API_KEY", "GALILEO_PROJECT", "GALILEO_LOG_STREAM"]
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {missing_vars}")
        return
    
    print("✅ Environment variables verified")
    
    # Test both modes
    modes = ["silly", "serious"]
    
    for mode in modes:
        print(f"\n🎯 Testing {mode.upper()} MODE")
        print("-" * 40)
        
        try:
            # Create LLM provider
            llm_config = LLMConfig(
                model="gpt-4",
                temperature=0.7,
                max_tokens=1000
            )
            llm_provider = OpenAIProvider(config=llm_config)
            
            # Create agent with logger
            logger = ConsoleAgentLogger(f"test-agent-{mode}")
            agent = SimpleAgent(
                verbosity="low",
                logger=logger,
                llm_provider=llm_provider,
                mode=mode
            )
            
            # Test parameters
            test_params = {
                "task": f"Generate a {mode} startup pitch",
                "industry": "Technology",
                "audience": "Young professionals",
                "random_word": "innovation"
            }
            
            print(f"📝 Executing agent with parameters: {json.dumps(test_params, indent=2)}")
            
            # Execute the agent
            result = await agent.run(**test_params)
            
            # Parse the result
            try:
                parsed_result = json.loads(result)
                print(f"✅ Agent execution completed successfully")
                print(f"📊 Result summary:")
                print(f"   - Mode: {parsed_result.get('mode', 'unknown')}")
                print(f"   - Tools used: {parsed_result.get('tools_used', [])}")
                print(f"   - Execution status: {parsed_result.get('execution_status', 'unknown')}")
                print(f"   - Output length: {len(parsed_result.get('final_output', ''))} characters")
                
                # Extract the actual pitch from the nested structure
                final_output = parsed_result.get('final_output', '')
                if isinstance(final_output, str):
                    try:
                        # Try to parse the final output as JSON to get the pitch
                        output_data = json.loads(final_output)
                        if 'pitch' in output_data:
                            pitch = output_data['pitch']
                            print(f"🎭 Generated pitch: {pitch[:100]}...")
                        else:
                            print(f"📄 Final output: {final_output[:100]}...")
                    except json.JSONDecodeError:
                        print(f"📄 Final output: {final_output[:100]}...")
                
            except json.JSONDecodeError as e:
                print(f"⚠️  Result is not valid JSON: {e}")
                print(f"📄 Raw result: {result[:200]}...")
            
            print(f"✅ {mode.capitalize()} mode test completed successfully")
            
        except Exception as e:
            print(f"❌ Error in {mode} mode test: {str(e)}")
            import traceback
            traceback.print_exc()
    
    print(f"\n🎉 Galileo logging test completed!")
    print(f"📊 Check your Galileo dashboard for:")
    print(f"   - Individual tool spans (hackernews_tool, news_api_tool, startup_simulator, serious_startup_simulator)")
    print(f"   - Agent workflow spans")
    print(f"   - Result formatting spans")
    print(f"   - Proper context passing between tools")
    print(f"   - Error handling and trace conclusions")

async def test_individual_tools():
    """Test individual tools to verify their Galileo logging"""
    
    print(f"\n🔧 Testing Individual Tools")
    print("=" * 40)
    
    # Import tools
    from tools.hackernews_tool import HackerNewsTool
    from tools.news_api_tool import NewsAPITool
    from tools.startup_simulator import StartupSimulatorTool
    from tools.serious_startup_simulator import SeriousStartupSimulatorTool
    
    tools_to_test = [
        ("HackerNews Tool", HackerNewsTool(), {"limit": 2}),
        ("News API Tool", NewsAPITool(), {"category": "business", "limit": 2}),
        ("Startup Simulator", StartupSimulatorTool(), {
            "industry": "Tech", 
            "audience": "Developers", 
            "random_word": "blockchain",
            "hn_context": "Sample HN context for testing"
        }),
        ("Serious Startup Simulator", SeriousStartupSimulatorTool(), {
            "industry": "Finance", 
            "audience": "Investors", 
            "random_word": "fintech",
            "news_context": "Sample news context for testing"
        })
    ]
    
    for tool_name, tool, params in tools_to_test:
        print(f"\n🔧 Testing {tool_name}")
        print("-" * 30)
        
        try:
            print(f"📝 Executing with parameters: {json.dumps(params, indent=2)}")
            
            # Execute the tool
            result = await tool.execute(**params)
            
            # Parse the result
            try:
                parsed_result = json.loads(result)
                print(f"✅ {tool_name} executed successfully")
                print(f"📊 Result type: {parsed_result.get('tool_result', 'unknown')}")
                
                # Show a snippet of the output
                if 'context' in parsed_result:
                    context = parsed_result['context']
                    print(f"📄 Context: {context[:100]}...")
                elif 'pitch' in parsed_result:
                    pitch = parsed_result['pitch']
                    print(f"🎭 Pitch: {pitch[:100]}...")
                
            except json.JSONDecodeError as e:
                print(f"⚠️  Result is not valid JSON: {e}")
                print(f"📄 Raw result: {result[:200]}...")
            
        except Exception as e:
            print(f"❌ Error testing {tool_name}: {str(e)}")

if __name__ == "__main__":
    print("🚀 Starting Galileo Logging Test Suite")
    print("=" * 60)
    
    # Run the tests
    asyncio.run(test_individual_tools())
    asyncio.run(test_galileo_logging())
    
    print(f"\n🎉 All tests completed!")
    print(f"📊 Check your Galileo dashboard for detailed traces and spans.") 