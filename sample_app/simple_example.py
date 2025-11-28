#!/usr/bin/env python3
"""
Simple LiteLLM Proxy Example

This is a minimal example showing how to use the LiteLLM proxy
instead of direct API calls.
"""

import openai
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def main():
    """Simple example of using LiteLLM proxy"""

    # Configure OpenAI client to use LiteLLM proxy
    client = openai.OpenAI(
        api_key=os.getenv('LITELLM_API_KEY', 'sk-1234567890'),  # Your LiteLLM API key
        base_url="http://localhost:4000/v1"  # Point to LiteLLM proxy
    )

    # Make a simple chat completion request
    try:
        print("🔄 Sending request to LiteLLM proxy...")

        response = client.chat.completions.create(
            model="gpt-4o-mini",  # This goes through LiteLLM proxy
            messages=[
                {"role": "user", "content": "Hello! Can you explain what you are?"}
            ],
            max_tokens=100,
            temperature=0.7
        )

        print("✅ Response received:")
        print(f"🤖 {response.choices[0].message.content}")

    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n💡 Make sure the LiteLLM proxy is running:")
        print("   docker-compose up -d")

if __name__ == "__main__":
    main()