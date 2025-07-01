import os
import json
from galileo import GalileoLogger, log
from galileo.openai import openai
from typing import Dict, Any
from agent_framework.tools.base import BaseTool
from agent_framework.models import ToolMetadata
from agent_framework.llm.models import LLMMessage
from agent_framework.utils.logging import get_galileo_logger
import asyncio
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# Use the Galileo-wrapped OpenAI client
client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

class StartupSimulatorTool(BaseTool):
    """Tool for generating a silly startup pitch using OpenAI's API"""
    
    def __init__(self):
        super().__init__()
        self.name = "startup_simulator"
        self.description = "Generate a creative startup pitch based on industry, audience, and a random word"
        # Get the centralized Galileo logger
        self.galileo_logger = get_galileo_logger()

    @classmethod
    def get_metadata(cls) -> ToolMetadata:
        return ToolMetadata(
            name="startup_simulator",
            description="Generates a silly startup pitch using OpenAI's API, based on user input.",
            tags=["startup", "generator", "openai", "fun"],
            input_schema={
                "type": "object",
                "properties": {
                    "industry": {"type": "string", "description": "Industry for the startup"},
                    "audience": {"type": "string", "description": "Target audience"},
                    "random_word": {"type": "string", "description": "A random word to include"},
                    "hn_context": {"type": "string", "description": "Recent HackerNews context for inspiration"}
                },
                "required": ["industry", "audience", "random_word"]
            },
            output_schema={
                "type": "string",
                "description": "JSON string containing silly startup pitch data with metadata"
            }
        )

    @log(span_type="tool", name="startup_simulator")
    async def execute(self, industry: str, audience: str, random_word: str, hn_context: str = "") -> str:
        """Execute the startup simulator tool with individual Galileo trace"""
        
        # Log inputs as JSON
        inputs = {
            "industry": industry,
            "audience": audience, 
            "random_word": random_word,
            "hn_context": hn_context[:200] + "..." if len(hn_context) > 200 else hn_context,
            "mode": "silly"
        }
        print(f"Startup Simulator Inputs: {json.dumps(inputs, indent=2)}")
        
        # Use the centralized Galileo logger
        logger = self.galileo_logger
        if not logger:
            print("⚠️  Warning: Galileo logger not available, proceeding without logging")
            # Fallback to direct API call without Galileo
            return await self._execute_without_galileo(industry, audience, random_word, hn_context)
        
        # Start individual trace for this tool
        trace = logger.start_trace(f"Startup Simulator - {industry} targeting {audience}")
        
        try:
            # Add LLM span for tool execution start
            logger.add_llm_span(
                input=f"Generate startup pitch for {industry} targeting {audience} with word '{random_word}'",
                output="Tool execution started",
                model="startup_simulator",
                num_input_tokens=len(str(inputs)),
                num_output_tokens=0,
                total_tokens=len(str(inputs)),
                duration_ns=0
            )
            
            # Create the prompt with HackerNews context
            hn_context_prompt = ""
            if hn_context:
                hn_context_prompt = f"\n\nUse these recent HackerNews stories for inspiration:\n{hn_context}"
            
            prompt = (
                f"Generate a creative and engaging startup pitch for a {industry} company "
                f"targeting {audience}. The pitch must include the word '{random_word}' naturally. "
                f"Make it fun, innovative, and memorable. Keep it under 500 characters total."
                f"{hn_context_prompt}"
            )
            
            # Create messages with Galileo context
            messages = [{"role": "user", "content": prompt}]
            
            # Execute the API call
            response = client.chat.completions.create(
                messages=messages,
                model="gpt-4"
            )
            
            # Extract the response
            pitch = response.choices[0].message.content.strip()
            
            # Create structured output
            output = {
                "pitch": pitch,
                "character_count": len(pitch),
                "mode": "silly",
                "hn_context_used": bool(hn_context),
                "timestamp": datetime.now().isoformat(),
                "model": "gpt-4",
                "input_tokens": response.usage.prompt_tokens if hasattr(response.usage, 'prompt_tokens') else 0,
                "output_tokens": response.usage.completion_tokens if hasattr(response.usage, 'completion_tokens') else 0,
                "total_tokens": response.usage.total_tokens if hasattr(response.usage, 'total_tokens') else 0
            }
            
            # Log output as JSON to console and for Galileo observability
            output_log = {
                "tool_execution": "startup_simulator",
                "inputs": inputs,
                "output": output,
                "metadata": {
                    "character_count": output["character_count"],
                    "mode": output["mode"],
                    "hn_context_used": output["hn_context_used"],
                    "timestamp": output["timestamp"]
                }
            }
            print(f"Startup Simulator Output: {json.dumps(output_log, indent=2)}")
            
            # Add LLM span for tool completion with detailed metrics
            logger.add_llm_span(
                input=f"Startup pitch generation completed",
                output=pitch,
                model="gpt-4",
                num_input_tokens=output["input_tokens"],
                num_output_tokens=output["output_tokens"],
                total_tokens=output["total_tokens"],
                duration_ns=0
            )
            
            # Conclude the trace successfully
            logger.conclude(output=pitch, duration_ns=0)
            
            # Return JSON string for proper Galileo logging display
            galileo_output = {
                "tool_result": "startup_simulator",
                "formatted_output": json.dumps(output, indent=2),
                "pitch": output["pitch"],
                "metadata": output
            }
            
            # Return as formatted JSON string for Galileo
            return json.dumps(galileo_output, indent=2)
            
        except Exception as e:
            # Conclude the trace with error
            if logger:
                logger.conclude(output=str(e), duration_ns=0, error=True)
            
            raise e

    async def _execute_without_galileo(self, industry: str, audience: str, random_word: str, hn_context: str = "") -> str:
        """Fallback execution without Galileo logging"""
        # Create the prompt with HackerNews context
        hn_context_prompt = ""
        if hn_context:
            hn_context_prompt = f"\n\nUse these recent HackerNews stories for inspiration:\n{hn_context}"
        
        prompt = (
            f"Generate a creative and engaging startup pitch for a {industry} company "
            f"targeting {audience}. The pitch must include the word '{random_word}' naturally. "
            f"Make it fun, innovative, and memorable. Keep it under 500 characters total."
            f"{hn_context_prompt}"
        )
        
        # Create messages
        messages = [{"role": "user", "content": prompt}]
        
        # Execute the API call
        response = client.chat.completions.create(
            messages=messages,
            model="gpt-4"
        )
        
        # Extract the response
        pitch = response.choices[0].message.content.strip()
        
        # Create structured output
        output = {
            "pitch": pitch,
            "character_count": len(pitch),
            "mode": "silly",
            "hn_context_used": bool(hn_context),
            "timestamp": datetime.now().isoformat(),
            "model": "gpt-4",
            "input_tokens": response.usage.prompt_tokens if hasattr(response.usage, 'prompt_tokens') else 0,
            "output_tokens": response.usage.completion_tokens if hasattr(response.usage, 'completion_tokens') else 0,
            "total_tokens": response.usage.total_tokens if hasattr(response.usage, 'total_tokens') else 0
        }
        
        # Return as formatted JSON string
        galileo_output = {
            "tool_result": "startup_simulator",
            "formatted_output": json.dumps(output, indent=2),
            "pitch": output["pitch"],
            "metadata": output
        }
        
        return json.dumps(galileo_output, indent=2) 