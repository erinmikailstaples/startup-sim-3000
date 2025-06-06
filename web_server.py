#!/usr/bin/env python3

import asyncio
import json
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from agent import SimpleAgent
from agent_framework.llm.openai_provider import OpenAIProvider
from agent_framework.llm.models import LLMConfig
from galileo import galileo_context
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    """Serve the main page"""
    return render_template('index.html')

@app.route('/api/generate', methods=['POST'])
def generate_startup():
    """API endpoint to generate startup pitch"""
    try:
        data = request.json
        industry = data.get('industry', '').strip()
        audience = data.get('audience', '').strip()
        random_word = data.get('randomWord', '').strip()
        mode = data.get('mode', 'silly').strip()  # Default to silly mode
        
        # Log API request as JSON
        api_request = {
            "endpoint": "/api/generate",
            "method": "POST",
            "inputs": {
                "industry": industry,
                "audience": audience,
                "random_word": random_word,
                "mode": mode
            },
            "timestamp": asyncio.get_event_loop().time()
        }
        print(f"API Request: {json.dumps(api_request, indent=2)}")
        
        if not industry or not audience or not random_word:
            return jsonify({'error': 'All fields are required'}), 400
        
        # Run the agent asynchronously
        result = asyncio.run(run_agent(industry, audience, random_word, mode))
        
        # Log API response as JSON
        api_response = {
            "endpoint": "/api/generate",
            "status": "success",
            "result_length": len(result),
            "mode": mode,
            "timestamp": asyncio.get_event_loop().time()
        }
        print(f"API Response: {json.dumps(api_response, indent=2)}")
        
        return jsonify({'result': result})
        
    except Exception as e:
        print(f"Error generating startup: {e}")
        return jsonify({'error': str(e)}), 500

async def run_agent(industry: str, audience: str, random_word: str, mode: str = "silly") -> str:
    """Run the agent to generate startup pitch"""
    # Set up LLM provider
    llm_provider = OpenAIProvider(config=LLMConfig(model="gpt-4", temperature=0.7))
    
    # Create agent instance with mode
    agent = SimpleAgent(llm_provider=llm_provider, mode=mode)
    
    # Create different task descriptions based on mode
    if mode == "serious":
        task = (
            f"First, get recent business news context from NewsAPI to understand current market trends, then "
            f"generate a professional startup business plan for a {industry} company targeting {audience} "
            f"that incorporates the concept '{random_word}'. Use the news context to inform market analysis "
            f"and competitive landscape. Make this extremely professional and corporate."
        )
    else:  # silly mode
        task = (
            f"First, get some inspiration from recent HackerNews stories, then "
            f"generate a startup pitch for a {industry} company targeting {audience} "
            f"that includes the word '{random_word}'. Make the pitch creative and "
            f"incorporate relevant trends from the HackerNews stories."
        )
    
    # Run the agent within Galileo context with mode-specific metadata
    context_name = f"startup_generator_{mode}_mode"
    with galileo_context(project="erin-custom-metric", log_stream="my_log_stream"):
        result = await agent.run(task)
        return result

if __name__ == '__main__':
    # Ensure Galileo environment variables are set
    if not os.getenv("GALILEO_API_KEY"):
        print("Warning: GALILEO_API_KEY not set. Galileo logging will be disabled.")
    
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY not set. Please set this environment variable.")
        exit(1)
    
    app.run(debug=True, host='0.0.0.0', port=2021)
