import os
import json
import aiohttp
import asyncio
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from agent_framework.models import ToolMetadata
from agent_framework.tools.base import BaseTool
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@dataclass
class NewsArticle:
    """Data class to represent a news article"""
    title: str
    description: Optional[str]
    url: str
    source: str
    author: Optional[str]
    published_at: str

class NewsAPITool(BaseTool):
    """Tool for fetching recent news articles using NewsAPI"""
    
    BASE_URL = "https://newsapi.org/v2"
    
    @classmethod
    def get_metadata(cls) -> ToolMetadata:
        """Get metadata for the tool registration"""
        return ToolMetadata(
            name="news_api_tool",
            description="Fetch recent news articles to check for similar startups and market trends",
            tags=["news", "api", "market-research", "startups"],
            input_schema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query for news articles (optional)"
                    },
                    "category": {
                        "type": "string",
                        "description": "News category (business, technology, etc.)"
                    },
                    "country": {
                        "type": "string", 
                        "description": "Country code (default: us)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of articles to fetch (default: 5)"
                    }
                }
            },
            output_schema={
                "type": "object",
                "properties": {
                    "articles": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "title": {"type": "string"},
                                "description": {"type": "string"},
                                "url": {"type": "string"},
                                "source": {"type": "string"},
                                "author": {"type": "string"},
                                "published_at": {"type": "string"}
                            }
                        }
                    },
                    "total_results": {"type": "integer"}
                }
            }
        )
    
    def __init__(self):
        super().__init__()
        self._session = None
        self.api_key = os.getenv("NEWS_API_KEY")
        if not self.api_key:
            raise ValueError("NEWS_API_KEY not found in environment variables")
    
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
    
    async def get_top_headlines(self, 
                               country: str = "us", 
                               category: Optional[str] = None,
                               limit: int = 5) -> List[NewsArticle]:
        """Fetch top headlines"""
        try:
            session = await self.session
            
            params = {
                "country": country,
                "apiKey": self.api_key,
                "pageSize": limit
            }
            
            if category:
                params["category"] = category
            
            async with session.get(f"{self.BASE_URL}/top-headlines", params=params) as response:
                response.raise_for_status()
                data = await response.json()
                
                if data.get("status") != "ok":
                    raise Exception(f"NewsAPI error: {data.get('message', 'Unknown error')}")
                
                articles = []
                for article_data in data.get("articles", []):
                    if article_data.get("title") and article_data.get("title") != "[Removed]":
                        articles.append(NewsArticle(
                            title=article_data.get("title", ""),
                            description=article_data.get("description"),
                            url=article_data.get("url", ""),
                            source=article_data.get("source", {}).get("name", "Unknown"),
                            author=article_data.get("author"),
                            published_at=article_data.get("publishedAt", "")
                        ))
                
                return articles
                
        except Exception as e:
            print(f"Error fetching top headlines: {str(e)}")
            return []
    
    async def search_articles(self, 
                             query: str, 
                             limit: int = 5) -> List[NewsArticle]:
        """Search for articles by query"""
        try:
            session = await self.session
            
            params = {
                "q": query,
                "apiKey": self.api_key,
                "pageSize": limit,
                "sortBy": "relevancy",
                "language": "en"
            }
            
            async with session.get(f"{self.BASE_URL}/everything", params=params) as response:
                response.raise_for_status()
                data = await response.json()
                
                if data.get("status") != "ok":
                    raise Exception(f"NewsAPI error: {data.get('message', 'Unknown error')}")
                
                articles = []
                for article_data in data.get("articles", []):
                    if article_data.get("title") and article_data.get("title") != "[Removed]":
                        articles.append(NewsArticle(
                            title=article_data.get("title", ""),
                            description=article_data.get("description"),
                            url=article_data.get("url", ""),
                            source=article_data.get("source", {}).get("name", "Unknown"),
                            author=article_data.get("author"),
                            published_at=article_data.get("publishedAt", "")
                        ))
                
                return articles
                
        except Exception as e:
            print(f"Error searching articles: {str(e)}")
            return []

    async def execute(self, **inputs: Any) -> str:
        """Execute the NewsAPI tool"""
        query = inputs.get('query')
        category = inputs.get('category')
        country = inputs.get('country', 'us')
        limit = inputs.get('limit', 5)
        
        # Log inputs as JSON
        input_data = {
            "query": query,
            "category": category,
            "country": country,
            "limit": limit,
            "api_source": "NewsAPI"
        }
        print(f"NewsAPI Tool Inputs: {json.dumps(input_data, indent=2)}")
        
        try:
            if query:
                # Search for specific articles
                articles = await self.search_articles(query, limit)
            else:
                # Get top headlines
                articles = await self.get_top_headlines(country, category, limit)
            
            # Prepare output as JSON
            output = {
                "articles": [article.__dict__ for article in articles],
                "total_results": len(articles),
                "query_type": "search" if query else "headlines",
                "category": category,
                "country": country,
                "limit": limit
            }
            
            # Log output as JSON to console and for Galileo observability
            output_log = {
                "tool_execution": "news_api_tool",
                "inputs": input_data,
                "output": output,
                "metadata": {
                    "total_results": output["total_results"],
                    "query_type": output["query_type"],
                    "category": output["category"],
                    "country": output["country"],
                    "limit": output["limit"],
                    "api_source": "NewsAPI"
                }
            }
            print(f"NewsAPI Tool Output: {json.dumps(output_log, indent=2)}")
            
            # Return JSON string for proper Galileo logging display
            galileo_output = {
                "tool_result": "news_api_tool",
                "formatted_output": json.dumps(output, indent=2),
                "articles": output["articles"],
                "metadata": output
            }
            
            # Return as formatted JSON string for Galileo
            return json.dumps(galileo_output, indent=2)
            
        finally:
            # Ensure session is closed
            if self._session and not self._session.closed:
                await self._session.close()

# Example usage
if __name__ == "__main__":
    async def main():
        async with NewsAPITool() as news:
            # Test top headlines
            result = await news.execute(category="business", limit=3)
            print("Top Business Headlines:")
            for article in result["articles"]:
                print(f"- {article['title']} ({article['source']})")
            
            # Test search
            result = await news.execute(query="startup funding", limit=3)
            print("\nStartup Funding News:")
            for article in result["articles"]:
                print(f"- {article['title']} ({article['source']})")
    
    asyncio.run(main())
