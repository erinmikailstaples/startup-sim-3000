import os
import json
from galileo.openai import openai
from galileo import GalileoLogger
from typing import Dict, Any
from agent_framework.tools.base import BaseTool
from agent_framework.models import ToolMetadata
from agent_framework.llm.models import LLMMessage
import asyncio
from dotenv import load_dotenv
from agent_framework.utils.logging import get_galileo_logger

# Load environment variables
load_dotenv()

class SeriousStartupSimulatorTool(BaseTool):
    """Tool for generating serious, professional startup pitches"""
    
    def __init__(self):
        super().__init__()
        # Initialize Galileo Logger using centralized instance
        self.galileo_logger = get_galileo_logger()

    @classmethod
    def get_metadata(cls) -> ToolMetadata:
        return ToolMetadata(
            name="serious_startup_simulator",
            description="Generates professional, dry, and boring startup pitches for serious business contexts",
            tags=["startup", "generator", "business", "professional", "serious"],
            input_schema={
                "type": "object",
                "properties": {
                    "industry": {"type": "string", "description": "Industry for the startup"},
                    "audience": {"type": "string", "description": "Target audience"},
                    "random_word": {"type": "string", "description": "A word to incorporate"},
                    "news_context": {"type": "string", "description": "Recent news context for market analysis"}
                },
                "required": ["industry", "audience", "random_word"]
            },
            output_schema={
                "type": "string",
                "description": "JSON string containing professional startup pitch data with metadata"
            }
        )

    async def execute(self, industry: str, audience: str, random_word: str, news_context: str = "") -> str:
        """Generate a serious, professional startup pitch"""
        
        # Log inputs as JSON
        inputs = {
            "industry": industry,
            "audience": audience,
            "random_word": random_word,
            "news_context": news_context[:200] + "..." if len(news_context) > 200 else news_context,
            "mode": "serious"
        }
        print(f"Serious Startup Simulator Inputs: {json.dumps(inputs, indent=2)}")
        
        # Galileo trace management is handled by the context manager
        # No need for manual trace creation, conclusion, or flushing here
        
        news_context_prompt = ""
        if news_context:
            news_context_prompt = f"\n\nRecent market context:\n{news_context}\n\nUse this context to inform your market analysis and competitive landscape."
        
        prompt = f"""
        You are a business consultant creating a concise startup pitch for a venture capital presentation. 

        Generate a professional, corporate business proposal in EXACTLY 500 characters or less with the following requirements:
        - Industry: {industry}
        - Target Market: {audience} 
        - Core Technology/Concept: Must incorporate "{random_word}" as a key component
        
        {news_context_prompt}
        
        Create a single, dense paragraph that includes:
        - Business concept overview
        - Market opportunity 
        - Competitive advantage
        - Revenue model
        
        Make this extremely dry and corporate. Use buzzwords like "synergistic value propositions," "scalable infrastructure," "market penetration strategies," and "sustainable competitive advantages."
        
        Be formal, avoid humor, and keep it under 500 characters total.
        """
        
        # Initialize async OpenAI client with Galileo integration
        client = openai.AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        
        # Create messages
        messages = [{"role": "user", "content": prompt}]
        
        # Execute the API call
        response = await client.chat.completions.create(
            messages=messages,
            model="gpt-4",
            temperature=0.3  # Lower temperature for more formal, consistent output
        )
        
        content = response.choices[0].message.content.strip()
        
        # Ensure it's under 500 characters
        if len(content) > 500:
            content = content[:497] + "..."
        
        # Prepare output as JSON
        output = {
            "pitch": content,
            "character_count": len(content),
            "mode": "serious",
            "market_analysis": "",
            "financial_projections": "",
            "competitive_landscape": "",
            "timestamp": response.created if hasattr(response, 'created') else None,
            "news_context_used": bool(news_context)
        }
        
        # Log output as JSON to console and for Galileo observability
        output_log = {
            "tool_execution": "serious_startup_simulator",
            "inputs": inputs,
            "output": output,
            "metadata": {
                "character_count": output["character_count"],
                "mode": output["mode"],
                "news_context_used": output["news_context_used"],
                "timestamp": output["timestamp"]
            }
        }
        print(f"Serious Startup Simulator Output: {json.dumps(output_log, indent=2)}")
        
        # Return JSON string for proper Galileo logging display
        galileo_output = {
            "tool_result": "serious_startup_simulator",
            "formatted_output": json.dumps(output, indent=2),
            "pitch": output["pitch"],
            "metadata": output
        }
        
        return json.dumps(galileo_output, indent=2)
    
    def _parse_business_pitch(self, content: str) -> Dict[str, str]:
        """Parse the business pitch into structured sections"""
        sections = {}
        
        # Simple parsing - look for section headers
        current_section = None
        current_content = []
        
        for line in content.split('\n'):
            line = line.strip()
            if not line:
                continue
                
            # Check if this is a section header
            if any(header in line.upper() for header in ['EXECUTIVE SUMMARY', 'MARKET ANALYSIS', 'COMPETITIVE LANDSCAPE', 'FINANCIAL PROJECTIONS']):
                if current_section:
                    sections[current_section] = '\n'.join(current_content).strip()
                
                if 'MARKET ANALYSIS' in line.upper():
                    current_section = 'market_analysis'
                elif 'COMPETITIVE LANDSCAPE' in line.upper():
                    current_section = 'competitive_landscape'
                elif 'FINANCIAL PROJECTIONS' in line.upper():
                    current_section = 'financial_projections'
                else:
                    current_section = 'executive_summary'
                
                current_content = []
            else:
                current_content.append(line)
        
        # Don't forget the last section
        if current_section and current_content:
            sections[current_section] = '\n'.join(current_content).strip()
        
        return sections
