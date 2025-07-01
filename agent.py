#!/usr/bin/env python3
"""
Simple Agent for Startup Pitch Generation
This agent generates startup pitches using different tools based on the selected mode.
"""

import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from dotenv import load_dotenv
from galileo import GalileoLogger
from galileo.openai import openai

from agent_framework.agent import Agent
from agent_framework.models import VerbosityLevel, ToolSelectionHooks
from agent_framework.llm.openai_provider import OpenAIProvider
from agent_framework.llm.models import LLMConfig
from agent_framework.utils.logging import ConsoleAgentLogger
from agent_framework.utils.tool_hooks import LoggingToolHooks, LoggingToolSelectionHooks

# Import all available tools
from tools.startup_simulator import StartupSimulatorTool
from tools.serious_startup_simulator import SeriousStartupSimulatorTool
from tools.hackernews_tool import HackerNewsTool
from tools.news_api_tool import NewsAPITool
from tools.text_analysis import TextAnalyzerTool
from tools.keyword_extraction import KeywordExtractorTool

# Load environment variables
load_dotenv()

# Use the Galileo-wrapped OpenAI client
client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

class SimpleAgent(Agent):
    """
    A simple agent that generates startup pitches.
    
    This agent demonstrates:
    1. Tool-based architecture with specialized tools
    2. Mode-based execution (silly vs serious)
    3. Galileo observability with proper span logging
    4. Context-aware tool execution
    """

    def __init__(
        self,
        verbosity: VerbosityLevel = VerbosityLevel.LOW,
        logger: Optional[ConsoleAgentLogger] = None,
        tool_selection_hooks: Optional[ToolSelectionHooks] = None,
        metadata: Optional[Dict[str, Any]] = None,
        llm_provider: Optional[OpenAIProvider] = None,
        mode: str = "silly",
    ):
        # Create default LLM config if not provided
        if llm_provider is None:
            llm_config = LLMConfig(
                model="gpt-4",
                temperature=0.7,
                max_tokens=1000
            )
            llm_provider = OpenAIProvider(config=llm_config)
        
        # Initialize the base Agent class with configuration
        super().__init__(
            agent_id=f"startup-agent-{mode}",
            verbosity=verbosity,
            logger=logger or ConsoleAgentLogger(f"startup-agent-{mode}"),
            tool_selection_hooks=tool_selection_hooks or LoggingToolSelectionHooks(logger or ConsoleAgentLogger(f"startup-agent-{mode}")),
            metadata=metadata or {},
            llm_provider=llm_provider
        )
        
        self.mode = mode
        self.task_parameters = {}
        
        # Register all available tools
        self._register_tools()
        
        # Set up logger with tool hooks
        if self.logger:
            self._setup_logger(self.logger)

    def _register_tools(self) -> None:
        """
        Register all available tools with the agent's tool registry.
        
        Think of tools as specialized functions that the agent can call.
        Each tool has:
        - A name and description
        - Input/output schemas (what it expects and returns)
        - Tags for categorization
        - An implementation (the actual code that runs)
        
        The agent will automatically choose which tools to use based on the task.
        """
        
        # Text analysis tool - can analyze and process text content
        self.tool_registry.register(
            metadata=TextAnalyzerTool.get_metadata(),
            implementation=TextAnalyzerTool
        )
        
        # Keyword extraction tool - finds important words/phrases in text
        self.tool_registry.register(
            metadata=KeywordExtractorTool.get_metadata(),
            implementation=KeywordExtractorTool
        )
        
        # Startup simulator tool - generates silly, creative startup pitches
        # Used in "silly" mode
        self.tool_registry.register(
            metadata=StartupSimulatorTool.get_metadata(),
            implementation=StartupSimulatorTool
        )
        
        # Serious startup simulator tool - generates professional business plans
        # Used in "serious" mode
        self.tool_registry.register(
            metadata=SeriousStartupSimulatorTool.get_metadata(),
            implementation=SeriousStartupSimulatorTool
        )
        
        # HackerNews tool - fetches trending tech stories for inspiration
        # Used in "silly" mode to get creative context
        self.tool_registry.register(
            metadata=HackerNewsTool.get_metadata(),
            implementation=HackerNewsTool
        )
        
        # NewsAPI tool - fetches business news for market analysis
        # Used in "serious" mode to get professional context
        self.tool_registry.register(
            metadata=NewsAPITool.get_metadata(),
            implementation=NewsAPITool
        )

    async def _format_result(self, task: str, results: List[tuple[str, Any]]) -> str:
        """
        Format the final result from tool executions.
        
        This method takes the raw outputs from all the tools and formats them
        into a coherent, user-friendly response. It's like the final step in
        a recipe where you plate the dish nicely.
        
        Args:
            task: The original user request
            results: List of (tool_name, result) tuples from executed tools
            
        Returns:
            Formatted string response for the user
        """
        # Initialize Galileo logger for this operation
        galileo_logger = GalileoLogger(
            project=os.environ.get("GALILEO_PROJECT"),
            log_stream=os.environ.get("GALILEO_LOG_STREAM")
        )
        
        # Start trace for result formatting
        trace = galileo_logger.start_trace("format_result")
        
        try:
            # Add span for formatting start
            galileo_logger.add_llm_span(
                input=f"Formatting results for task: {task}",
                output="Formatting started",
                model="result_formatter",
                num_input_tokens=len(str(results)),
                num_output_tokens=0,
                total_tokens=len(str(results)),
                duration_ns=0
            )
            
            # Check for silly mode first - look for startup_simulator tool results
            for tool_name, result in results:
                if tool_name == "startup_simulator":
                    # Parse the JSON string result from Galileo-formatted output
                    try:
                        if isinstance(result, str):
                            parsed_result = json.loads(result)
                            pitch = parsed_result.get("pitch", "")
                        else:
                            # Fallback for dict format (shouldn't happen now)
                            pitch = result.get("pitch", "")
                        
                        # Log full structured result to Galileo for observability
                        result_data = {
                            "tool": tool_name,
                            "mode": "silly",
                            "full_result": result,
                            "extracted_pitch": pitch
                        }
                        print(f"Agent Result Data (Silly): {json.dumps(result_data, indent=2)}")
                        
                        # Add span for formatting completion
                        galileo_logger.add_llm_span(
                            input=f"Result formatting completed for {tool_name}",
                            output=pitch,
                            model="result_formatter",
                            num_input_tokens=len(str(result)),
                            num_output_tokens=len(pitch),
                            total_tokens=len(str(result)) + len(pitch),
                            duration_ns=0
                        )
                        
                        # Conclude the trace successfully
                        galileo_logger.conclude(output=pitch, duration_ns=0)
                        
                        return pitch
                    except json.JSONDecodeError as e:
                        print(f"Error parsing silly mode result: {e}")
                        galileo_logger.conclude(output=str(result), duration_ns=0, error=True)
                        return str(result)
            
            # Check for serious mode - look for serious_startup_simulator tool results
            for tool_name, result in results:
                if tool_name == "serious_startup_simulator":
                    # Parse the JSON string result from Galileo-formatted output
                    try:
                        if isinstance(result, str):
                            parsed_result = json.loads(result)
                            pitch = parsed_result.get("pitch", "")
                        else:
                            # Fallback for dict format (shouldn't happen now)
                            pitch = result.get("pitch", "")
                        
                        # Log full structured result to Galileo for observability
                        result_data = {
                            "tool": tool_name,
                            "mode": "serious",
                            "full_result": result,
                            "extracted_pitch": pitch
                        }
                        print(f"Agent Result Data (Serious): {json.dumps(result_data, indent=2)}")
                        
                        # Add span for formatting completion
                        galileo_logger.add_llm_span(
                            input=f"Result formatting completed for {tool_name}",
                            output=pitch,
                            model="result_formatter",
                            num_input_tokens=len(str(result)),
                            num_output_tokens=len(pitch),
                            total_tokens=len(str(result)) + len(pitch),
                            duration_ns=0
                        )
                        
                        # Conclude the trace successfully
                        galileo_logger.conclude(output=pitch, duration_ns=0)
                        
                        return pitch
                    except json.JSONDecodeError as e:
                        print(f"Error parsing serious mode result: {e}")
                        galileo_logger.conclude(output=str(result), duration_ns=0, error=True)
                        return str(result)
            
            # No valid result found
            galileo_logger.conclude(output="No startup pitch generated.", duration_ns=0)
            return "No startup pitch generated."
            
        except Exception as e:
            # Conclude the trace with error
            galileo_logger.conclude(output=str(e), duration_ns=0, error=True)
            raise e

    async def _execute_hackernews_tool(self, limit: int = 3) -> str:
        """Execute HackerNews tool with proper Galileo logging"""
        # Initialize Galileo logger for this tool execution
        galileo_logger = GalileoLogger(
            project=os.environ.get("GALILEO_PROJECT"),
            log_stream=os.environ.get("GALILEO_LOG_STREAM")
        )
        
        # Start trace for HackerNews tool
        trace = galileo_logger.start_trace(f"execute_hackernews_tool")
        
        try:
            # Add span for tool execution start
            galileo_logger.add_llm_span(
                input=f"Executing HackerNews tool with limit: {limit}",
                output="Tool execution started",
                model="hackernews_tool",
                num_input_tokens=len(str(limit)),
                num_output_tokens=0,
                total_tokens=len(str(limit)),
                duration_ns=0
            )
            
            hn_tool_class = self.tool_registry.get_implementation("hackernews_tool")
            if hn_tool_class:
                hn_tool = hn_tool_class()
                hn_context = await hn_tool.execute(limit=limit)
                
                # Add span for tool completion
                galileo_logger.add_llm_span(
                    input=f"HackerNews tool execution completed",
                    output=hn_context[:200] + "..." if len(hn_context) > 200 else hn_context,
                    model="hackernews_tool",
                    num_input_tokens=len(str(limit)),
                    num_output_tokens=len(hn_context),
                    total_tokens=len(str(limit)) + len(hn_context),
                    duration_ns=0
                )
                
                # Conclude the trace successfully
                galileo_logger.conclude(output=hn_context, duration_ns=0)
                
                return hn_context
            
            # Tool not found
            galileo_logger.conclude(output="", duration_ns=0, error=True)
            return ""
            
        except Exception as e:
            # Conclude the trace with error
            galileo_logger.conclude(output=str(e), duration_ns=0, error=True)
            raise e

    async def _execute_news_api_tool(self, category: str = "business", limit: int = 5) -> str:
        """Execute News API tool with proper Galileo logging"""
        # Initialize Galileo logger for this tool execution
        galileo_logger = GalileoLogger(
            project=os.environ.get("GALILEO_PROJECT"),
            log_stream=os.environ.get("GALILEO_LOG_STREAM")
        )
        
        # Start trace for News API tool
        trace = galileo_logger.start_trace(f"execute_news_api_tool")
        
        try:
            # Add span for tool execution start
            galileo_logger.add_llm_span(
                input=f"Executing News API tool with category: {category}, limit: {limit}",
                output="Tool execution started",
                model="news_api_tool",
                num_input_tokens=len(str(category)) + len(str(limit)),
                num_output_tokens=0,
                total_tokens=len(str(category)) + len(str(limit)),
                duration_ns=0
            )
            
            news_tool_class = self.tool_registry.get_implementation("news_api_tool")
            if news_tool_class:
                news_tool = news_tool_class()
                news_context = await news_tool.execute(category=category, limit=limit)
                
                # Add span for tool completion
                galileo_logger.add_llm_span(
                    input=f"News API tool execution completed",
                    output=news_context[:200] + "..." if len(news_context) > 200 else news_context,
                    model="news_api_tool",
                    num_input_tokens=len(str(category)) + len(str(limit)),
                    num_output_tokens=len(news_context),
                    total_tokens=len(str(category)) + len(str(limit)) + len(news_context),
                    duration_ns=0
                )
                
                # Conclude the trace successfully
                galileo_logger.conclude(output=news_context, duration_ns=0)
                
                return news_context
            
            # Tool not found
            galileo_logger.conclude(output="", duration_ns=0, error=True)
            return ""
            
        except Exception as e:
            # Conclude the trace with error
            galileo_logger.conclude(output=str(e), duration_ns=0, error=True)
            raise e

    async def _execute_startup_simulator(self, industry: str, audience: str, random_word: str, hn_context: str = "") -> str:
        """Execute startup simulator tool with proper Galileo logging"""
        # Initialize Galileo logger for this tool execution
        galileo_logger = GalileoLogger(
            project=os.environ.get("GALILEO_PROJECT"),
            log_stream=os.environ.get("GALILEO_LOG_STREAM")
        )
        
        # Start trace for startup simulator tool
        trace = galileo_logger.start_trace(f"execute_startup_simulator")
        
        try:
            # Add span for tool execution start
            galileo_logger.add_llm_span(
                input=f"Executing startup simulator for {industry} targeting {audience} with word '{random_word}'",
                output="Tool execution started",
                model="startup_simulator",
                num_input_tokens=len(industry) + len(audience) + len(random_word) + len(hn_context),
                num_output_tokens=0,
                total_tokens=len(industry) + len(audience) + len(random_word) + len(hn_context),
                duration_ns=0
            )
            
            startup_tool_class = self.tool_registry.get_implementation("startup_simulator")
            if startup_tool_class:
                startup_tool = startup_tool_class()
                startup_result = await startup_tool.execute(
                    industry=industry,
                    audience=audience,
                    random_word=random_word,
                    hn_context=hn_context
                )
                
                # Add span for tool completion
                galileo_logger.add_llm_span(
                    input=f"Startup simulator execution completed",
                    output=startup_result[:200] + "..." if len(startup_result) > 200 else startup_result,
                    model="startup_simulator",
                    num_input_tokens=len(industry) + len(audience) + len(random_word) + len(hn_context),
                    num_output_tokens=len(startup_result),
                    total_tokens=len(industry) + len(audience) + len(random_word) + len(hn_context) + len(startup_result),
                    duration_ns=0
                )
                
                # Conclude the trace successfully
                galileo_logger.conclude(output=startup_result, duration_ns=0)
                
                return startup_result
            
            # Tool not found
            galileo_logger.conclude(output="", duration_ns=0, error=True)
            return ""
            
        except Exception as e:
            # Conclude the trace with error
            galileo_logger.conclude(output=str(e), duration_ns=0, error=True)
            raise e

    async def _execute_serious_startup_simulator(self, industry: str, audience: str, random_word: str, news_context: str = "") -> str:
        """Execute serious startup simulator tool with proper Galileo logging"""
        # Initialize Galileo logger for this tool execution
        galileo_logger = GalileoLogger(
            project=os.environ.get("GALILEO_PROJECT"),
            log_stream=os.environ.get("GALILEO_LOG_STREAM")
        )
        
        # Start trace for serious startup simulator tool
        trace = galileo_logger.start_trace(f"execute_serious_startup_simulator")
        
        try:
            # Add span for tool execution start
            galileo_logger.add_llm_span(
                input=f"Executing serious startup simulator for {industry} targeting {audience} with word '{random_word}'",
                output="Tool execution started",
                model="serious_startup_simulator",
                num_input_tokens=len(industry) + len(audience) + len(random_word) + len(news_context),
                num_output_tokens=0,
                total_tokens=len(industry) + len(audience) + len(random_word) + len(news_context),
                duration_ns=0
            )
            
            startup_tool_class = self.tool_registry.get_implementation("serious_startup_simulator")
            if startup_tool_class:
                startup_tool = startup_tool_class()
                startup_result = await startup_tool.execute(
                    industry=industry,
                    audience=audience,
                    random_word=random_word,
                    news_context=news_context
                )
                
                # Add span for tool completion
                galileo_logger.add_llm_span(
                    input=f"Serious startup simulator execution completed",
                    output=startup_result[:200] + "..." if len(startup_result) > 200 else startup_result,
                    model="serious_startup_simulator",
                    num_input_tokens=len(industry) + len(audience) + len(random_word) + len(news_context),
                    num_output_tokens=len(startup_result),
                    total_tokens=len(industry) + len(audience) + len(random_word) + len(news_context) + len(startup_result),
                    duration_ns=0
                )
                
                # Conclude the trace successfully
                galileo_logger.conclude(output=startup_result, duration_ns=0)
                
                return startup_result
            
            # Tool not found
            galileo_logger.conclude(output="", duration_ns=0, error=True)
            return ""
            
        except Exception as e:
            # Conclude the trace with error
            galileo_logger.conclude(output=str(e), duration_ns=0, error=True)
            raise e

    async def run(self, task: str, industry: str = "", audience: str = "", random_word: str = "") -> str:
        """
        Execute the agent's task with Galileo monitoring.
        
        This is the main entry point for the agent. It orchestrates the entire process:
        1. Stores user parameters for tool execution
        2. Starts Galileo tracing for observability
        3. Executes tools in sequence with proper context passing
        4. Formats the final result
        
        Args:
            task: The user's request (e.g., "generate a startup pitch")
            industry: Target industry for the startup
            audience: Target audience for the startup
            random_word: Random word to include in the pitch
            
        Returns:
            Formatted startup pitch as a string
        """
        
        # Store parameters for tool execution
        # These will be passed to individual tools as needed
        self.task_parameters = {
            "industry": industry,
            "audience": audience, 
            "random_word": random_word
        }
        
        # Log workflow start as JSON for observability
        # This helps us understand the agent's decision-making process
        workflow_data = {
            "agent_id": self.agent_id,
            "mode": self.mode,
            "task": task,
            "start_time": datetime.now().isoformat(),
            "tools_registered": list(self.tool_registry.get_all_tools().keys())
        }
        print(f"Agent Workflow Start: {json.dumps(workflow_data, indent=2)}")
        
        # Initialize Galileo logger for this agent execution
        logger = GalileoLogger(
            project=os.environ.get("GALILEO_PROJECT"),
            log_stream=os.environ.get("GALILEO_LOG_STREAM")
        )
        
        # Start individual trace for this agent workflow
        trace = logger.start_trace(f"Agent Workflow - {self.mode} mode - {self.agent_id}")
        
        try:
            # Add LLM span for workflow start
            logger.add_llm_span(
                input=f"Agent workflow started for task: {task}",
                output="Workflow initialization",
                model="agent_workflow",
                num_input_tokens=len(task),
                num_output_tokens=0,
                total_tokens=len(task),
                duration_ns=0
            )
            
            # Execute tools based on mode with proper context passing
            results = []
            
            if self.mode == "serious":
                # Step 1: Get news context first
                print("🔍 Step 1: Fetching business news for context...")
                news_context = await self._execute_news_api_tool(category="business", limit=5)
                results.append(("news_api", news_context))
                
                # Step 2: Generate serious startup pitch using the news context
                print("📝 Step 2: Generating professional startup plan...")
                startup_result = await self._execute_serious_startup_simulator(
                    industry=industry,
                    audience=audience,
                    random_word=random_word,
                    news_context=news_context
                )
                results.append(("serious_startup_simulator", startup_result))
            
            else:  # silly mode
                # Step 1: Get HackerNews context first
                print("🔍 Step 1: Fetching HackerNews stories for inspiration...")
                hn_context = await self._execute_hackernews_tool(limit=3)
                results.append(("hackernews", hn_context))
                
                # Step 2: Generate silly startup pitch using the HN context
                print("🎭 Step 2: Generating creative startup pitch...")
                startup_result = await self._execute_startup_simulator(
                    industry=industry,
                    audience=audience,
                    random_word=random_word,
                    hn_context=hn_context
                )
                results.append(("startup_simulator", startup_result))
            
            # Step 3: Format the final result
            print("✨ Step 3: Formatting final result...")
            formatted_result = await self._format_result(task, results)
            
            # Log workflow completion as JSON
            completion_data = {
                "agent_id": self.agent_id,
                "mode": self.mode,
                "task": task,
                "end_time": datetime.now().isoformat(),
                "result_length": len(formatted_result),
                "tools_used": [result[0] for result in results],
                "execution_status": "success"
            }
            print(f"Agent Workflow Complete: {json.dumps(completion_data, indent=2)}")
            
            # Add LLM span for workflow completion
            logger.add_llm_span(
                input=f"Agent workflow completed successfully",
                output=formatted_result,
                model="agent_workflow",
                num_input_tokens=len(task),
                num_output_tokens=len(formatted_result),
                total_tokens=len(task) + len(formatted_result),
                duration_ns=0
            )
            
            # Conclude the trace successfully
            logger.conclude(output=formatted_result, duration_ns=0)
            
            # Prepare structured JSON output for Galileo workflow logging
            workflow_result = {
                "agent_id": self.agent_id,
                "mode": self.mode,
                "task": task,
                "final_output": formatted_result,
                "tools_used": [result[0] for result in results],
                "execution_status": "success",
                "timestamp": datetime.now().isoformat()
            }
            
            # Only call on_agent_done after all tools have completed
            if self.logger:
                await self.logger.on_agent_done(formatted_result, self.message_history)
            
            # Return structured JSON string for Galileo workflow logging
            return json.dumps(workflow_result, indent=2)
            
        except Exception as e:
            # Conclude the trace with error
            logger.conclude(output=str(e), duration_ns=0, error=True)
            
            raise e
        finally:
            # Only set end_time if current_task exists
            if hasattr(self, 'current_task') and self.current_task is not None:
                self.current_task.end_time = datetime.now()
                if self.current_task.status == "in_progress":
                    self.current_task.status = "completed"
            self._current_plan = None  # Clear the plan 