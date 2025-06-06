# AGENT.md - Startum Sim 3000 Development Guide

## Run Commands
- **Start app**: `python run_startup_sim.py`
- **Test**: No test framework configured yet
- **Lint**: No linter configured yet  
- **Type check**: No type checker configured yet

## Dependencies
- Python 3.x with virtual environment (`venv/`)
- Core: `langchain`, `openai`, `langgraph`, `pydantic`, `galileo` 
- UI: `rich` for console output
- Config: `python-dotenv` for environment variables

## Code Style
- **Imports**: Group stdlib, third-party, local imports with blank lines between
- **Types**: Use type hints extensively (`typing` module, `Optional`, `Dict`, `List`, `Any`)
- **Async**: Prefer async/await patterns for I/O operations
- **Classes**: Use abstract base classes (`ABC`) for extensible designs
- **Naming**: snake_case for functions/variables, PascalCase for classes
- **Error Handling**: Custom exceptions in `agent_framework/exceptions.py`
- **Logging**: Use `galileo` integration and `rich` console for output

## Architecture
- `agent_framework/`: Core agent framework with tools, state, LLM providers
- `tools/`: Tool implementations (startup simulator, text analysis, etc.)
- Entry points: `run_startup_sim.py`, `agent.py`
