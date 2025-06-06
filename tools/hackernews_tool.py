import json
import aiohttp
from typing import Dict, Optional, List, Any
from dataclasses import dataclass
from datetime import datetime
import time
from galileo import log, galileo_context
from agent_framework.models import ToolMetadata
from agent_framework.tools.base import BaseTool

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
        self._session = None
    
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
    async def execute(self, **inputs: Any) -> Dict[str, Any]:
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
        
        try:
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
            
            # Log output as JSON
            print(f"HackerNews Tool Output: {json.dumps(output, indent=2)}")
            
            return output
        finally:
            # Ensure session is closed
            if self._session and not self._session.closed:
                await self._session.close()

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