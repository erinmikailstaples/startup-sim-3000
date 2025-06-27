from typing import Any, Dict, List, Optional
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
import time
import os
import json
from uuid import uuid4
from datetime import datetime
from dotenv import load_dotenv
from galileo import GalileoLogger

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
        
        # Initialize Galileo Logger
        project_id = os.getenv("GALILEO_PROJECT_ID", "erin-custom-metric")
        log_stream = os.getenv("GALILEO_LOG_STREAM", "my_log_stream")
        self.galileo_logger = GalileoLogger(project=project_id, log_stream=log_stream)
        
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

    async def _format_result(self, task: str, results: List[tuple[str, Any]]) -> str:
        """Format the final result from tool executions"""
        # Check for silly mode first
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
                    
                    # Log full structured result to Galileo
                    result_data = {
                        "tool": tool_name,
                        "mode": "silly",
                        "full_result": result,
                        "extracted_pitch": pitch
                    }
                    print(f"Agent Result Data (Silly): {json.dumps(result_data, indent=2)}")
                    return pitch
                except json.JSONDecodeError as e:
                    print(f"Error parsing silly mode result: {e}")
                    return str(result)
        
        # Check for serious mode
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
                    
                    # Log full structured result to Galileo
                    result_data = {
                        "tool": tool_name,
                        "mode": "serious",
                        "full_result": result,
                        "extracted_pitch": pitch
                    }
                    print(f"Agent Result Data (Serious): {json.dumps(result_data, indent=2)}")
                    return pitch
                except json.JSONDecodeError as e:
                    print(f"Error parsing serious mode result: {e}")
                    return str(result)
        
        return "No startup pitch generated."

    async def run(self, task: str, industry: str = "", audience: str = "", random_word: str = "") -> str:
        """Execute the agent's task with Galileo monitoring"""
        
        # Store parameters for tool execution
        self.task_parameters = {
            "industry": industry,
            "audience": audience, 
            "random_word": random_word
        }
        
        # Start Galileo trace with structured input
        trace_input = {
            "user_task": task,
            "agent_mode": self.mode,
            "agent_id": self.agent_id,
            "timestamp": datetime.now().isoformat()
        }
        
        # Log workflow start as JSON
        workflow_data = {
            "agent_id": self.agent_id,
            "mode": self.mode,
            "task": task,
            "start_time": datetime.now().isoformat(),
            "tools_registered": list(self.tool_registry.get_all_tools().keys())
        }
        print(f"Agent Workflow Start: {json.dumps(workflow_data, indent=2)}")
        
        # Start Galileo trace with string metadata
        try:
            trace = self.galileo_logger.start_trace(
                input=json.dumps(trace_input, indent=2),
                name=f"Startup Generator - {self.mode.title()} Mode",
                metadata={
                    "agent_id": str(self.agent_id),
                    "mode": str(self.mode),
                    "tools_count": str(len(self.tool_registry.get_all_tools().keys()))
                },
                tags=["startup-generator", f"mode-{self.mode}", "agent-workflow"]
            )
            print(f"Galileo trace started successfully for agent workflow")
        except Exception as e:
            print(f"Warning: Could not start Galileo trace for agent: {e}")
            trace = None
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
                    # Parse JSON string result
                    try:
                        if isinstance(result, str):
                            parsed_result = json.loads(result)
                            articles = parsed_result.get("articles", [])
                        else:
                            # Fallback for dict format
                            articles = result.get("articles", [])
                        
                        if articles:
                            context = "Recent business news:\n"
                            for article in articles[:3]:
                                context += f"- {article['title']} ({article['source']})\n"
                            print("\nContext from NewsAPI:")
                            print(context)
                        else:
                            context = ""
                    except json.JSONDecodeError as e:
                        print(f"Error parsing NewsAPI result: {e}")
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
                    # Parse JSON string result
                    try:
                        if isinstance(result, str):
                            parsed_result = json.loads(result)
                            stories = parsed_result.get("stories", [])
                        else:
                            # Fallback for dict format
                            stories = result.get("stories", [])
                        
                        if stories:
                            context = "Recent HackerNews stories:\n"
                            for story in stories:
                                context += f"- {story['title']}\n"
                            print("\nContext from HackerNews:")
                            print(context)
                        else:
                            context = ""
                    except json.JSONDecodeError as e:
                        print(f"Error parsing HackerNews result: {e}")
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
                tool_name = step["tool"]
                
                # Add LLM span for each tool execution
                llm_input = {
                    "tool": tool_name,
                    "task": task,
                    "mode": self.mode,
                    "step_details": step
                }
                
                result = await self._execute_step(step, task, self._current_plan)
                
                # Add LLM span to Galileo trace (only if trace was created successfully)
                if trace is not None:
                    try:
                        self.galileo_logger.add_llm_span(
                            input=json.dumps(llm_input, indent=2),
                            output=str(result)[:1000] + "..." if len(str(result)) > 1000 else str(result),
                            model="gpt-4",  # The underlying model used by tools
                            name=f"{tool_name} Execution"
                        )
                    except Exception as e:
                        print(f"Warning: Could not add LLM span for {tool_name}: {e}")
                
                results.append((step["tool"], result))
            
            # Format the results using our custom HN style
            formatted_result = await self._format_result(task, results)
            self.current_task.output = formatted_result
            
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
            
            # Prepare structured JSON output for Galileo workflow logging
            workflow_result = {
                "workflow_type": "agent_execution",
                "agent_metadata": {
                    "agent_id": self.agent_id,
                    "mode": self.mode,
                    "tools_registered": list(self.tool_registry.get_all_tools().keys())
                },
                "execution_summary": {
                    "task": task,
                    "start_time": workflow_data["start_time"],
                    "end_time": datetime.now().isoformat(),
                    "tools_used": [result[0] for result in results],
                    "execution_status": "success"
                },
                "final_output": formatted_result,
                "tool_results": [{"tool": tool_name, "result_preview": str(result)[:200] + "..." if len(str(result)) > 200 else str(result)} for tool_name, result in results]
            }
            
            # Conclude Galileo trace with final output (this is key for custom metrics)
            if trace is not None:
                try:
                    self.galileo_logger.conclude(output=json.dumps(workflow_result, indent=2))
                    print(f"Galileo trace concluded successfully for agent workflow")
                except Exception as e:
                    print(f"Warning: Could not conclude Galileo trace: {e}")
            
            # Flush traces to Galileo
            try:
                self.galileo_logger.flush()
            except Exception as e:
                print(f"Warning: Could not flush Galileo traces: {e}")
            
            # Only call on_agent_done after all tools have completed
            if self.logger:
                await self.logger.on_agent_done(formatted_result, self.message_history)
            
            # Return structured JSON string for Galileo workflow logging
            return json.dumps(workflow_result, indent=2)
            
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