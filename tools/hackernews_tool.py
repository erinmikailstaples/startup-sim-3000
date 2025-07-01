import os
import json
import aiohttp
from galileo import log
from typing import Dict, Optional, List, Any
from dataclasses import dataclass
from datetime import datetime
import time
from agent_framework.models import ToolMetadata
from agent_framework.tools.base import BaseTool
from agent_framework.utils.logging import get_galileo_logger
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@dataclass
class HNStory:
    """Data class to represent a Hacker News story"""
    id: int
    title: str
    url: Optional[str]
    score: int
    by: str
    time: int
    text: Optional[str]
    descendants: int  # number of comments
    type: str

class HackerNewsTool(BaseTool):
    """Tool for interacting with Hacker News API and formatting content in HN style"""
    
    BASE_URL = "https://hacker-news.firebaseio.com/v0"
    
    @classmethod
    def get_metadata(cls) -> ToolMetadata:
        """Get metadata for the tool registration"""
        return ToolMetadata(
            name="hackernews_tool",
            description="A tool for interacting with Hacker News API and formatting content in HN style",
            tags=["news", "api", "hackernews"],
            input_schema={
                "type": "object",
                "properties": {
                    "story_id": {
                        "type": "integer",
                        "description": "The ID of the Hacker News story to fetch"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of top stories to fetch (default: 10)"
                    }
                }
            },
            output_schema={
                "type": "object",
                "properties": {
                    "stories": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "integer"},
                                "title": {"type": "string"},
                                "url": {"type": "string"},
                                "score": {"type": "integer"},
                                "by": {"type": "string"},
                                "time": {"type": "integer"},
                                "text": {"type": "string"},
                                "descendants": {"type": "integer"},
                                "type": {"type": "string"}
                            }
                        }
                    }
                }
            }
        )
    
    def __init__(self):
        super().__init__()
        self.name = "hackernews_tool"
        self.description = "A tool for interacting with Hacker News API and formatting content in HN style"
        self._session = None
        # Get the centralized Galileo logger
        self.galileo_logger = get_galileo_logger()
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self._session and not self._session.closed:
            await self._session.close()
    
    @property
    async def session(self) -> aiohttp.ClientSession:
        """Get or create an aiohttp session"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session
    
    async def get_story(self, story_id: int) -> Optional[HNStory]:
        """Fetch a story by its ID"""
        try:
            session = await self.session
            async with session.get(f"{self.BASE_URL}/item/{story_id}.json") as response:
                    response.raise_for_status()
                    data = await response.json()
                    
                    if not data:
                        return None
                        
                    return HNStory(
                        id=data.get('id'),
                        title=data.get('title', ''),
                        url=data.get('url'),
                        score=data.get('score', 0),
                        by=data.get('by', ''),
                        time=data.get('time', 0),
                        text=data.get('text'),
                        descendants=data.get('descendants', 0),
                        type=data.get('type', 'story')
                    )
        except Exception as e:
            print(f"Error fetching story {story_id}: {str(e)}")
            return None
    
    async def get_top_stories(self, limit: int = 10) -> List[int]:
        """Get IDs of top stories"""
        try:
            session = await self.session
            async with session.get(f"{self.BASE_URL}/topstories.json") as response:
                    response.raise_for_status()
                    return (await response.json())[:limit]
        except Exception as e:
            print(f"Error fetching top stories: {str(e)}")
            return []
    
    def format_story_text(self, story: HNStory) -> str:
        """Format story text in HN style"""
        timestamp = datetime.fromtimestamp(story.time)
        time_ago = self._get_time_ago(timestamp)
        
        # Format the story text in HN style
        formatted_text = f"""
{story.title}
{story.score} points by {story.by} {time_ago} | {story.descendants} comments

{story.text if story.text else ''}
"""
        return formatted_text.strip()
    
    def _get_time_ago(self, timestamp: datetime) -> str:
        """Convert timestamp to 'X time ago' format"""
        now = datetime.now()
        diff = now - timestamp
        
        if diff.days > 0:
            return f"{diff.days} days ago"
        elif diff.seconds >= 3600:
            hours = diff.seconds // 3600
            return f"{hours} hours ago"
        elif diff.seconds >= 60:
            minutes = diff.seconds // 60
            return f"{minutes} minutes ago"
        else:
            return "just now"
    
    def get_story_style(self, story: HNStory) -> Dict:
        """Get styling information for a story"""
        return {
            "score": story.score,
            "author": story.by,
            "comment_count": story.descendants,
            "timestamp": story.time,
            "type": story.type
        }

    @log(span_type="tool", name="hackernews_tool")
    async def execute(self, **inputs: Any) -> str:
        """Execute the HackerNews tool"""
        story_id = inputs.get('story_id')
        limit = inputs.get('limit', 10)
        
        # Log inputs as JSON
        input_data = {
            "story_id": story_id,
            "limit": limit,
            "api_source": "HackerNews"
        }
        print(f"HackerNews Tool Inputs: {json.dumps(input_data, indent=2)}")
        
        # Use the centralized Galileo logger
        logger = self.galileo_logger
        if not logger:
            print("⚠️  Warning: Galileo logger not available, proceeding without logging")
            return await self._execute_without_galileo(limit)
        
        # Start individual trace for this tool
        trace = logger.start_trace(f"HackerNews Tool - Fetching {limit} stories")
        
        try:
            # Add span for tool execution start
            logger.add_llm_span(
                input=f"Fetching {limit} trending HackerNews stories",
                output="Tool execution started",
                model="hackernews_api",
                num_input_tokens=len(str(input_data)),
                num_output_tokens=0,
                total_tokens=len(str(input_data)),
                duration_ns=0
            )
            
            if story_id is not None:
                story = await self.get_story(story_id)
                stories = [story.__dict__] if story else []
            else:
                # Get top stories
                story_ids = await self.get_top_stories(limit=limit)
                stories = []
                for sid in story_ids:
                    story = await self.get_story(sid)
                    if story:
                        stories.append(story.__dict__)
            
            # Prepare output as JSON
            output = {
                "stories": stories,
                "total_stories": len(stories),
                "limit": limit,
                "story_id": story_id
            }
            
            # Log output as JSON to console and for Galileo observability
            output_log = {
                "tool_execution": "hackernews_tool",
                "inputs": input_data,
                "output": output,
                "metadata": {
                    "total_stories": output["total_stories"],
                    "limit": output["limit"],
                    "api_source": "HackerNews"
                }
            }
            print(f"HackerNews Tool Output: {json.dumps(output_log, indent=2)}")
            
            # Add span for tool completion
            logger.add_llm_span(
                input=f"HackerNews stories fetched successfully",
                output=json.dumps(output, indent=2),
                model="hackernews_api",
                num_input_tokens=len(str(input_data)),
                num_output_tokens=len(json.dumps(output, indent=2)),
                total_tokens=len(str(input_data)) + len(json.dumps(output, indent=2)),
                duration_ns=0
            )
            
            # Conclude the trace successfully
            logger.conclude(output=json.dumps(output, indent=2), duration_ns=0)
            
            # Return JSON string for proper Galileo logging display
            galileo_output = {
                "tool_result": "hackernews_tool",
                "formatted_output": json.dumps(output, indent=2),
                "stories": output["stories"],
                "metadata": output
            }
            
            return json.dumps(galileo_output, indent=2)
        except Exception as e:
            # Conclude the trace with error
            if logger:
                logger.conclude(output=str(e), duration_ns=0, error=True)
            
            raise e

    async def _execute_without_galileo(self, limit: int = 3) -> str:
        """Fallback execution without Galileo logging"""
        # Fetch top story IDs
        async with aiohttp.ClientSession() as session:
            async with session.get('https://hacker-news.firebaseio.com/v0/topstories.json') as response:
                if response.status != 200:
                    raise Exception(f"Failed to fetch top stories: {response.status}")
                
                story_ids = await response.json()
                story_ids = story_ids[:limit]  # Get only the requested number
                
                # Fetch individual story details
                stories = []
                for story_id in story_ids:
                    async with session.get(f'https://hacker-news.firebaseio.com/v0/item/{story_id}.json') as story_response:
                        if story_response.status == 200:
                            story_data = await story_response.json()
                            if story_data and 'title' in story_data:
                                stories.append({
                                    'id': story_data.get('id'),
                                    'title': story_data.get('title'),
                                    'url': story_data.get('url'),
                                    'score': story_data.get('score', 0),
                                    'by': story_data.get('by'),
                                    'time': story_data.get('time')
                                })
        
        # Format stories for context
        formatted_stories = []
        for story in stories:
            formatted_stories.append(f"• {story['title']} (Score: {story['score']})")
        
        context = "\n".join(formatted_stories)
        
        # Create structured output
        output = {
            "stories": stories,
            "formatted_context": context,
            "story_count": len(stories),
            "requested_limit": limit,
            "timestamp": datetime.now().isoformat(),
            "source": "hackernews"
        }
        
        # Return as formatted JSON string
        galileo_output = {
            "tool_result": "hackernews_tool",
            "formatted_output": json.dumps(output, indent=2),
            "context": context,
            "metadata": output
        }
        
        return json.dumps(galileo_output, indent=2)

# Example usage
if __name__ == "__main__":
    async def main():
        async with HackerNewsTool() as hn:
            top_stories = await hn.get_top_stories(limit=1)
            if top_stories:
                story = await hn.get_story(top_stories[0])
                if story:
                    print(hn.format_story_text(story))

    import asyncio
    asyncio.run(main()) 