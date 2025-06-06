from typing import Any, Dict, List, Optional
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
import time
import os
from dotenv import load_dotenv
from galileo import galileo_context, log

from agent_framework.agent import Agent
from agent_framework.state import AgentState
from agent_framework.models import VerbosityLevel, ToolSelectionHooks
from agent_framework.llm.models import LLMConfig
from agent_framework.llm.openai_provider import OpenAIProvider
from agent_framework.utils.logging import AgentLogger
from tools.text_analysis import TextAnalyzerTool
from tools.keyword_extraction import KeywordExtractorTool
from tools.startup_simulator import StartupSimulatorTool
from tools.hackernews_tool import HackerNewsTool

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
    ):
        super().__init__(
            verbosity=verbosity,
            logger=logger,
            tool_selection_hooks=tool_selection_hooks,
            metadata=metadata,
            llm_provider=llm_provider
        )
        self.state = AgentState()
        
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
        
        # HackerNews tool
        self.tool_registry.register(
            metadata=HackerNewsTool.get_metadata(),
            implementation=HackerNewsTool
        )

    async def _format_result(self, task: str, results: List[tuple[str, Dict[str, Any]]]) -> str:
        """Format the final result from tool executions"""
        formatted_result = []
        
        # First, get HackerNews stories if available
        hn_stories = None
        for tool_name, result in results:
            if tool_name == "hackernews_tool" and "stories" in result:
                hn_stories = result["stories"]
                break
        
        # Format HackerNews stories if available
        if hn_stories:
            formatted_result.append("\nContext from HackerNews:")
            formatted_result.append("Recent HackerNews stories:")
            for story in hn_stories[:3]:  # Show top 3 stories
                formatted_result.append(f"- {story['title']}")
            formatted_result.append("")
        
        # Then format the main result (startup pitch)
        for tool_name, result in results:
            if tool_name == "startup_simulator" and "pitch" in result:
                formatted_result.append("\nYour silly startup pitch:")
                formatted_result.append(result["pitch"])
                break
        
        return "\n".join(formatted_result)

    @log(span_type="agent", name="execute")
    async def execute(self, task: str) -> str:
        """Execute the agent's task with Galileo monitoring"""
        with galileo_context(project="erin-custom-metric", log_stream="my_log_stream"):
            # First, get some context from HackerNews
            try:
                # Get the HackerNews tool implementation
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

            # Execute the main task
            try:
                # Use run() instead of execute()
                results = await super().run(task)
                
                # Format the results using HN style
                formatted_result = await self._format_result(task, results)
                return formatted_result
            except Exception as e:
                print(f"Error during task execution: {e}")
                return f"Error: {str(e)}" 