import os
import json
from galileo.openai import openai
from galileo import log, galileo_context
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
                    "random_word": {"type": "string", "description": "A random word to include"}
                },
                "required": ["industry", "audience", "random_word"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "pitch": {"type": "string", "description": "A silly startup pitch (max 500 chars)"}
                }
            }
        )

    @log(span_type="tool", name="startup_simulator")
    async def execute(self, industry: str, audience: str, random_word: str) -> Dict[str, Any]:
        """Generate a silly startup pitch using the LLM provider"""
        
        # Log inputs as JSON
        inputs = {
            "industry": industry,
            "audience": audience, 
            "random_word": random_word,
            "mode": "silly"
        }
        print(f"Startup Simulator Inputs: {json.dumps(inputs, indent=2)}")
        
        prompt = (
            f"Create a silly, creative startup pitch in 500 characters or less. "
            f"The startup is in the '{industry}' industry, targets '{audience}', and must include the word '{random_word}'. "
            f"Make it fun and a little absurd!"
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
            "timestamp": response.created if hasattr(response, 'created') else None
        }
        
        # Log output as JSON
        print(f"Startup Simulator Output: {json.dumps(output, indent=2)}")
        
        return output 