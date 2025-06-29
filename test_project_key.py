#!/usr/bin/env python3
"""
Test script to verify project-based OpenAI API key functionality
"""

import asyncio
import os
from dotenv import load_dotenv
from openai import AsyncOpenAI

# Load environment variables
load_dotenv()

async def test_project_key():
    """Test if the project-based key works"""
    
    # Get the API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ No API key found in environment")
        return
    
    print(f"🔑 Testing API key: {api_key[:20]}...")
    
    # Check if it's a project key
    is_project_key = api_key.startswith("sk-proj-")
    print(f"📋 Key type: {'Project-based' if is_project_key else 'Regular'}")
    
    if is_project_key:
        # Extract project ID
        parts = api_key.split('-')
        if len(parts) >= 3:
            project_id = parts[2]
            print(f"🏗️  Project ID: {project_id}")
    
    try:
        # Create client
        client = AsyncOpenAI(api_key=api_key)
        print("✅ Client created successfully")
        
        # Test a simple API call
        print("🔄 Testing API call...")
        response = await client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": "Say 'Hello, project key works!'"}],
            max_tokens=50
        )
        
        result = response.choices[0].message.content
        print(f"✅ API call successful!")
        print(f"🤖 Response: {result}")
        
    except Exception as e:
        print(f"❌ API call failed: {e}")
        print(f"🔍 Error type: {type(e).__name__}")
        
        # Provide specific guidance based on error
        if "401" in str(e):
            print("\n💡 401 Error suggests authentication issue:")
            print("   - Check if the project key is valid")
            print("   - Ensure the project exists in your OpenAI account")
            print("   - Verify the project has the necessary permissions")
        elif "403" in str(e):
            print("\n💡 403 Error suggests permission issue:")
            print("   - Check if the project has access to the model you're using")
            print("   - Verify billing is set up for the project")
        elif "404" in str(e):
            print("\n💡 404 Error suggests resource not found:")
            print("   - Check if the project ID is correct")
            print("   - Verify the project exists")

if __name__ == "__main__":
    asyncio.run(test_project_key()) 