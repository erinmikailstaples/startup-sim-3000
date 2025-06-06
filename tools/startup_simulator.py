import os
import json
from galileo.openai import openai
from galileo import log
from typing import Dict, Any
from agent_framework.tools.base import BaseTool
from agent_framework.models import ToolMetadata
from agent_framework.llm.models import LLMMessage
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class StartupSimulatorTool(BaseTool):
    """Tool for generating a silly startup pitch using OpenAI's API"""

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
    async def execute(self, industry: str, audience: str, random_word: str, hn_context: str = "") -> Dict[str, Any]:
        """Generate a silly startup pitch using the LLM provider"""
        
        # Log inputs as JSON
        inputs = {
            "industry": industry,
            "audience": audience, 
            "random_word": random_word,
            "hn_context": hn_context[:200] + "..." if len(hn_context) > 200 else hn_context,
            "mode": "silly"
        }
        print(f"Startup Simulator Inputs: {json.dumps(inputs, indent=2)}")
        
        hn_context_prompt = ""
        if hn_context:
            hn_context_prompt = f"\n\nRecent HackerNews context:\n{hn_context}\n\nUse this context to make your pitch even more creative and relevant to current tech trends."
        
        prompt = (
            f"Create a silly, creative startup pitch in 500 characters or less. "
            f"The startup is in the '{industry}' industry, targets '{audience}', and must include the word '{random_word}'. "
            f"Make it fun and a little absurd!"
            f"{hn_context_prompt}"
        )
        
        # Initialize async OpenAI client with Galileo integration
        client = openai.AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        
        # Create messages with Galileo context
        messages = [{"role": "user", "content": prompt}]
        
        # Execute the API call (Galileo context inherited from parent workflow)
        response = await client.chat.completions.create(
            messages=messages,
            model="gpt-4"
        )
        
        pitch = response.choices[0].message.content.strip()[:500]
        
        # Prepare output as JSON
        output = {
            "pitch": pitch,
            "character_count": len(pitch),
            "mode": "silly",
            "timestamp": response.created if hasattr(response, 'created') else None,
            "hn_context_used": bool(hn_context)
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
        
        # Return JSON string for proper Galileo logging display
        galileo_output = {
            "tool_result": "startup_simulator",
            "formatted_output": json.dumps(output, indent=2),
            "pitch": output["pitch"],
            "metadata": output
        }
        
        # Return as formatted JSON string for Galileo
        return json.dumps(galileo_output, indent=2) 