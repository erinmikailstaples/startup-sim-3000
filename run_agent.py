import asyncio
from agent import SimpleAgent
from agent_framework.llm.openai_provider import OpenAIProvider
from agent_framework.llm.models import LLMConfig
from galileo import galileo_context, log
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@log(span_type="workflow", name="agent_main")
async def main():
    # Ensure Galileo environment variables are set
    if not os.getenv("GALILEO_API_KEY"):
        print("Warning: GALILEO_API_KEY not set. Galileo logging will be disabled.")
    
    # Set up LLM provider
    llm_provider = OpenAIProvider(config=LLMConfig(model="gpt-4", temperature=0.7))

    # Create agent instance
    agent = SimpleAgent(llm_provider=llm_provider)

    # Prompt user for input
    print("\nWhat would you like to do?")
    print("1. Generate a startup pitch")
    print("2. Get recent HackerNews stories")
    print("3. Analyze text")
    choice = input("\nEnter your choice (1-3): ")

    # Run the agent within Galileo context
    with galileo_context(project="erin-custom-metric", log_stream="my_log_stream"):
        if choice == "1":
            industry = input("Enter an industry: ")
            audience = input("Enter a target audience: ")
            random_word = input("Enter a random word: ")
            task = f"Generate a startup pitch for a {industry} company targeting {audience} that includes the word '{random_word}'"
        elif choice == "2":
            task = "Get the top 5 stories from HackerNews and summarize them"
        elif choice == "3":
            text = input("Enter text to analyze: ")
            task = f"Analyze this text and extract key insights: {text}"
        else:
            print("Invalid choice!")
            return

        result = await agent.execute(task)
        print("\nResult:\n")
        print(result)

if __name__ == "__main__":
    asyncio.run(main())