import os
from dotenv import load_dotenv
from galileo import galileo_context
from galileo.openai import openai

# Load environment variables from .env
load_dotenv()

def call_openai():
    # This call will be automatically traced by Galileo
    client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    chat_completion = client.chat.completions.create(
        messages=[{"role": "user", "content": "Say this is a test"}],
        model="gpt-4o"
    )
    return chat_completion.choices[0].message.content

if __name__ == "__main__":
    # Initialize Galileo context globally using env vars
    galileo_context.init(
        project=os.environ.get("GALILEO_PROJECT"),
        log_stream=os.environ.get("GALILEO_LOG_STREAM")
    )
    # Optionally, wrap your main logic in a Galileo context for a single trace
    with galileo_context():
        result = call_openai()
        print("OpenAI result:", result)
        # Only call flush if you want to force-upload traces in a script
        galileo_context.flush()