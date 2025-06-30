import os
import json
from galileo.openai import openai
from galileo import GalileoLogger
from typing import Dict, Any
from agent_framework.tools.base import BaseTool
from agent_framework.models import ToolMetadata
import asyncio
from dotenv import load_dotenv
from agent_framework.utils.logging import GalileoLoggerWrapper

# Load environment variables
load_dotenv()

class SeriousStartupSimulatorTool(BaseTool):
    """Tool for generating serious, professional startup pitches"""
    
    def __init__(self):
        super().__init__()
        # Initialize Galileo Logger
        project_id = os.getenv("GALILEO_PROJECT_ID", "erin-custom-metric")
        log_stream = os.getenv("GALILEO_LOG_STREAM", "my_log_stream")
        self.galileo_logger = GalileoLoggerWrapper(project=project_id, log_stream=log_stream)

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
        
        # Start Galileo trace for this tool with string metadata
        try:
            trace = self.galileo_logger.start_trace(
                input=json.dumps(inputs, indent=2),
                name="Serious Startup Pitch Generation",
                metadata={
                    "tool": "serious_startup_simulator",
                    "mode": "serious",
                    "has_news_context": str(bool(news_context))
                },
                tags=["startup-generator", "serious-mode", "business-pitch"]
            )
            print(f"Galileo trace started successfully for serious startup simulator")
        except Exception as e:
            print(f"Warning: Could not start Galileo trace for serious simulator: {e}")
            trace = None
        
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
        
        # Add LLM span to Galileo trace (only if trace was created successfully)
        if trace is not None:
            try:
                self.galileo_logger.add_llm_span(
                    input=prompt,
                    output=content,
                    model="gpt-4",
                    name="Serious Pitch Generation"
                )
            except Exception as e:
                print(f"Warning: Could not add LLM span for serious simulator: {e}")
        
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
        
        # Conclude Galileo trace with final output (only if trace was created successfully)
        if trace is not None:
            try:
                self.galileo_logger.conclude(output=json.dumps(galileo_output, indent=2))
                print(f"Galileo trace concluded successfully for serious startup simulator")
            except Exception as e:
                print(f"Warning: Could not conclude Galileo trace for serious simulator: {e}")
        
        # Flush traces to Galileo
        try:
            self.galileo_logger.flush()
        except Exception as e:
            print(f"Warning: Could not flush Galileo traces from serious simulator: {e}")
        
        # Return as formatted JSON string for Galileo
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
