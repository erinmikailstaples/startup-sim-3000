import os
import json
import aiohttp
from galileo import log
from typing import Dict, Any, List
from agent_framework.tools.base import BaseTool
from agent_framework.models import ToolMetadata
from agent_framework.utils.logging import get_galileo_logger
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

class NewsAPITool(BaseTool):
    """Tool for fetching business news from NewsAPI"""
    
    def __init__(self):
        super().__init__()
        self.name = "news_api_tool"
        self.description = "Fetch business news articles for market analysis and professional context"
        self.api_key = os.environ.get("NEWS_API_KEY")
        # Get the centralized Galileo logger
        self.galileo_logger = get_galileo_logger()

    @classmethod
    def get_metadata(cls) -> ToolMetadata:
        return ToolMetadata(
            name="news_api_tool",
            description="Fetches business news articles for market analysis and professional context",
            tags=["news", "business", "market", "analysis"],
            input_schema={
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "News category to fetch",
                        "default": "business"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of articles to fetch",
                        "default": 5
                    }
                },
                "required": []
            },
            output_schema={
                "type": "string",
                "description": "JSON string containing news articles with metadata"
            }
        )

    @log(span_type="tool", name="news_api_tool")
    async def execute(self, category: str = "business", limit: int = 5) -> str:
        """Fetch business news articles"""
        
        # Log inputs
        inputs = {
            "category": category,
            "limit": limit,
            "timestamp": datetime.now().isoformat()
        }
        print(f"News API Tool Inputs: {json.dumps(inputs, indent=2)}")
        
        # Use the centralized Galileo logger
        logger = self.galileo_logger
        if not logger:
            print("⚠️  Warning: Galileo logger not available, proceeding without logging")
            return await self._execute_without_galileo(category, limit)
        
        # Start individual trace for this tool
        trace = logger.start_trace(f"News API Tool - Fetching {limit} {category} articles")
        
        try:
            # Add span for tool execution start
            logger.add_llm_span(
                input=f"Fetching {limit} {category} news articles",
                output="Tool execution started",
                model="news_api",
                num_input_tokens=len(str(inputs)),
                num_output_tokens=0,
                total_tokens=len(str(inputs)),
                duration_ns=0
            )
            
            if not self.api_key:
                raise Exception("NEWS_API_KEY not found in environment variables")
            
            # Fetch news articles
            url = f"https://newsapi.org/v2/top-headlines"
            params = {
                "country": "us",
                "category": category,
                "apiKey": self.api_key,
                "pageSize": limit
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status != 200:
                        raise Exception(f"Failed to fetch news: {response.status}")
                    
                    data = await response.json()
                    articles = data.get("articles", [])
            
            # Format articles for context
            formatted_articles = []
            for article in articles:
                title = article.get("title", "No title")
                description = article.get("description", "No description")
                formatted_articles.append(f"• {title}: {description}")
            
            context = "\n".join(formatted_articles)
            
            # Create structured output
            output = {
                "articles": articles,
                "formatted_context": context,
                "article_count": len(articles),
                "requested_limit": limit,
                "category": category,
                "timestamp": datetime.now().isoformat(),
                "source": "newsapi"
            }
            
            # Log output as JSON
            output_log = {
                "tool_execution": "news_api_tool",
                "inputs": inputs,
                "output": output,
                "metadata": {
                    "article_count": output["article_count"],
                    "requested_limit": output["requested_limit"],
                    "category": output["category"],
                    "timestamp": output["timestamp"]
                }
            }
            print(f"News API Tool Output: {json.dumps(output_log, indent=2)}")
            
            # Add span for tool completion
            logger.add_llm_span(
                input=f"News articles fetched successfully",
                output=context,
                model="news_api",
                num_input_tokens=len(str(inputs)),
                num_output_tokens=len(context),
                total_tokens=len(str(inputs)) + len(context),
                duration_ns=0
            )
            
            # Conclude the trace successfully
            logger.conclude(output=context, duration_ns=0)
            
            # Return JSON string for proper Galileo logging display
            galileo_output = {
                "tool_result": "news_api_tool",
                "formatted_output": json.dumps(output, indent=2),
                "context": context,
                "metadata": output
            }
            
            return json.dumps(galileo_output, indent=2)
            
        except Exception as e:
            # Conclude the trace with error
            if logger:
                logger.conclude(output=str(e), duration_ns=0, error=True)
            
            raise e

    async def _execute_without_galileo(self, category: str = "business", limit: int = 5) -> str:
        """Fallback execution without Galileo logging"""
        if not self.api_key:
            raise Exception("NEWS_API_KEY not found in environment variables")
        
        # Fetch news articles
        url = f"https://newsapi.org/v2/top-headlines"
        params = {
            "country": "us",
            "category": category,
            "apiKey": self.api_key,
            "pageSize": limit
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    raise Exception(f"Failed to fetch news: {response.status}")
                
                data = await response.json()
                articles = data.get("articles", [])
        
        # Format articles for context
        formatted_articles = []
        for article in articles:
            title = article.get("title", "No title")
            description = article.get("description", "No description")
            formatted_articles.append(f"• {title}: {description}")
        
        context = "\n".join(formatted_articles)
        
        # Create structured output
        output = {
            "articles": articles,
            "formatted_context": context,
            "article_count": len(articles),
            "requested_limit": limit,
            "category": category,
            "timestamp": datetime.now().isoformat(),
            "source": "newsapi"
        }
        
        # Return as formatted JSON string
        galileo_output = {
            "tool_result": "news_api_tool",
            "formatted_output": json.dumps(output, indent=2),
            "context": context,
            "metadata": output
        }
        
        return json.dumps(galileo_output, indent=2)

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
