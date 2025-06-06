from typing import Any, Dict, List, Optional
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
import time
import os
from uuid import uuid4
from datetime import datetime
from dotenv import load_dotenv
from galileo import galileo_context, log

from agent_framework.agent import Agent
from agent_framework.state import AgentState
from agent_framework.models import VerbosityLevel, ToolSelectionHooks, TaskExecution
from agent_framework.llm.models import LLMConfig
from agent_framework.llm.openai_provider import OpenAIProvider
from agent_framework.utils.logging import AgentLogger
from tools.text_analysis import TextAnalyzerTool
from tools.keyword_extraction import KeywordExtractorTool
from tools.startup_simulator import StartupSimulatorTool
from tools.serious_startup_simulator import SeriousStartupSimulatorTool
from tools.hackernews_tool import HackerNewsTool
from tools.news_api_tool import NewsAPITool

# Load environment variables
load_dotenv()

class SimpleAgent(Agent):
    """A simple agent that demonstrates basic functionality"""
    
    def __init__(
        self,
        verbosity: VerbosityLevel = VerbosityLevel.LOW,
        logger: Optional[AgentLogger] = None,
        tool_selection_hooks: Optional[ToolSelectionHooks] = None,
        metadata: Optional[Dict[str, Any]] = None,
        llm_provider: Optional[OpenAIProvider] = None,
        mode: str = "silly",
    ):
        super().__init__(
            verbosity=verbosity,
            logger=logger,
            tool_selection_hooks=tool_selection_hooks,
            metadata=metadata,
            llm_provider=llm_provider
        )
        self.state = AgentState()
        self.mode = mode
        
        # Set up template environment
        template_dir = Path(__file__).parent / "templates"
        self.template_env = Environment(
            loader=FileSystemLoader(template_dir),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Configure LLM provider if not provided
        if not self.llm_provider:
            llm_config = LLMConfig(
                model="gpt-4",
                temperature=0.7
            )
            self.llm_provider = OpenAIProvider(config=llm_config)
        
        # Register tools
        self._register_tools()

    def _register_tools(self) -> None:
        """Register all tools with the registry"""
        # Text analyzer
        self.tool_registry.register(
            metadata=TextAnalyzerTool.get_metadata(),
            implementation=TextAnalyzerTool
        )
        
        # Keyword extractor
        self.tool_registry.register(
            metadata=KeywordExtractorTool.get_metadata(),
            implementation=KeywordExtractorTool
        )
        
        # Startup simulator
        self.tool_registry.register(
            metadata=StartupSimulatorTool.get_metadata(),
            implementation=StartupSimulatorTool
        )
        
        # Serious startup simulator
        self.tool_registry.register(
            metadata=SeriousStartupSimulatorTool.get_metadata(),
            implementation=SeriousStartupSimulatorTool
        )
        
        # HackerNews tool
        self.tool_registry.register(
            metadata=HackerNewsTool.get_metadata(),
            implementation=HackerNewsTool
        )
        
        # NewsAPI tool
        self.tool_registry.register(
            metadata=NewsAPITool.get_metadata(),
            implementation=NewsAPITool
        )

    async def _format_result(self, task: str, results: List[tuple[str, Dict[str, Any]]]) -> str:
        """Format the final result from tool executions"""
        # Check for silly mode first
        for tool_name, result in results:
            if tool_name == "startup_simulator" and "pitch" in result:
                return result["pitch"]
        
        # Check for serious mode
        for tool_name, result in results:
            if tool_name == "serious_startup_simulator" and "pitch" in result:
                return result["pitch"]
        
        return "No startup pitch generated."

    @log(span_type="workflow", name="agent_execution")
    async def run(self, task: str) -> str:
        """Execute the agent's task with Galileo monitoring"""
        # Get context based on mode
        if self.mode == "serious":
            # For serious mode, get NewsAPI context
            try:
                news_tool_impl = self.tool_registry.get_implementation("news_api_tool")
                if not news_tool_impl:
                    raise ValueError("NewsAPI tool not found in registry")
                
                # Create an instance and execute it
                news_tool = news_tool_impl()
                async with news_tool:
                    result = await news_tool.execute(category="business", limit=5)
                    if "articles" in result and result["articles"]:
                        context = "Recent business news:\n"
                        for article in result["articles"][:3]:
                            context += f"- {article['title']} ({article['source']})\n"
                        print("\nContext from NewsAPI:")
                        print(context)
                    else:
                        context = ""
            except Exception as e:
                print(f"Warning: Could not fetch news articles: {e}")
                context = ""
        else:
            # For silly mode, get HackerNews context
            try:
                hn_tool_impl = self.tool_registry.get_implementation("hackernews_tool")
                if not hn_tool_impl:
                    raise ValueError("HackerNews tool not found in registry")
                
                # Create an instance and execute it
                hn_tool = hn_tool_impl()
                async with hn_tool:
                    result = await hn_tool.execute(limit=3)
                    if "stories" in result:
                        context = "Recent HackerNews stories:\n"
                        for story in result["stories"]:
                            context += f"- {story['title']}\n"
                        print("\nContext from HackerNews:")
                        print(context)
                    else:
                        context = ""
            except Exception as e:
                print(f"Warning: Could not fetch HackerNews stories: {e}")
                context = ""

        # Execute the main task by calling parent run but intercepting before final format
        try:
            self.current_task = TaskExecution(
                task_id=str(uuid4()),
                agent_id=self.agent_id,
                input=task,
                start_time=datetime.now(),
                steps=[]
            )

            if self.logger:
                self.logger.on_agent_start(task)

            # Store the context for use by tools
            self.context_data = context

            # Create a plan using chain of thought reasoning
            self._current_plan = await self.plan_task(task)
            
            # Execute each step in the plan to get raw results
            results = []
            for step in self._current_plan.execution_plan:
                result = await self._execute_step(step, task, self._current_plan)
                results.append((step["tool"], result))
            
            # Format the results using our custom HN style
            formatted_result = await self._format_result(task, results)
            self.current_task.output = formatted_result
            
            # Only call on_agent_done after all tools have completed
            if self.logger:
                await self.logger.on_agent_done(formatted_result, self.message_history)
            
            return formatted_result
            
        except Exception as e:
            self.current_task.error = str(e)
            self.current_task.status = "failed"
            print(f"Error during task execution: {e}")
            return f"Error: {str(e)}"
        finally:
            self.current_task.end_time = datetime.now()
            if self.current_task.status == "in_progress":
                self.current_task.status = "completed"
            self._current_plan = None  # Clear the plan 