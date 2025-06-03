import asyncio
from tools.startup_simulator import StartupSimulatorTool
from agent_framework.llm.openai_provider import OpenAIProvider
from agent_framework.llm.models import LLMConfig

async def main():
    # Prompt user for input
    industry = input("Enter an industry: ")
    audience = input("Enter a target audience: ")
    random_word = input("Enter a random word: ")

    # Set up LLM provider (adjust config as needed)
    llm_provider = OpenAIProvider(config=LLMConfig(model="gpt-4", temperature=0.7))

    # Create tool instance and set LLM provider
    tool = StartupSimulatorTool()
    tool.llm_provider = llm_provider

    # Run the tool
    result = await tool.execute(industry=industry, audience=audience, random_word=random_word)
    print("\nYour silly startup pitch:\n")
    print(result["pitch"])

if __name__ == "__main__":
    asyncio.run(main())