#!/usr/bin/env python3
"""
LiteLLM Proxy Sample Application

This sample application demonstrates how to use the LiteLLM proxy instead of
making direct API calls to LLM providers. It showcases various features including:
- Chat completions with different models
- Streaming responses
- Error handling and fallbacks
- Model switching
- Request customization
"""

import asyncio
import json
import os
import sys
from typing import Dict, List, Optional, AsyncGenerator
import openai
import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class LiteLLMClient:
    """Client for interacting with LiteLLM proxy"""

    def __init__(self, proxy_url: str = "http://localhost:4000", api_key: Optional[str] = None):
        """
        Initialize the LiteLLM client

        Args:
            proxy_url: URL of the LiteLLM proxy server
            api_key: API key for authentication (optional if proxy doesn't require auth)
        """
        self.proxy_url = proxy_url.rstrip('/')
        self.api_key = api_key or os.getenv('LITELLM_API_KEY')

        # Configure OpenAI client to use our proxy
        self.client = openai.OpenAI(
            api_key=self.api_key,
            base_url=f"{self.proxy_url}/v1"
        )

        # Async client for streaming
        self.async_client = openai.AsyncOpenAI(
            api_key=self.api_key,
            base_url=f"{self.proxy_url}/v1"
        )

    async def check_proxy_health(self) -> bool:
        """Check if the LiteLLM proxy is healthy"""
        try:
            async with httpx.AsyncClient() as client:
                headers = {"Authorization": f"Bearer {self.api_key}"}
                response = await client.get(f"{self.proxy_url}/health", headers=headers, timeout=5.0)
                return response.status_code == 200
        except Exception as e:
            print(f"❌ Proxy health check failed: {e}")
            return False

    async def list_models(self) -> List[str]:
        """Get list of available models from the proxy"""
        try:
            async with httpx.AsyncClient() as client:
                headers = {"Authorization": f"Bearer {self.api_key}"}
                response = await client.get(f"{self.proxy_url}/v1/models", headers=headers, timeout=10.0)

                if response.status_code == 200:
                    data = response.json()
                    return [model["id"] for model in data.get("data", [])]
                else:
                    print(f"❌ Failed to fetch models: {response.status_code}")
                    return []
        except Exception as e:
            print(f"❌ Error fetching models: {e}")
            return []

    def chat_completion(self, messages: List[Dict], model: str = "gpt-4o-mini", **kwargs) -> Optional[str]:
        """
        Send a chat completion request to the proxy

        Args:
            messages: List of message dictionaries
            model: Model name to use
            **kwargs: Additional parameters for the request
        """
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                **kwargs
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"❌ Chat completion failed: {e}")
            return None

    async def chat_completion_async(self, messages: List[Dict], model: str = "gpt-4o-mini", **kwargs) -> Optional[str]:
        """Async version of chat completion"""
        try:
            response = await self.async_client.chat.completions.create(
                model=model,
                messages=messages,
                **kwargs
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"❌ Async chat completion failed: {e}")
            return None

    async def chat_completion_stream(self, messages: List[Dict], model: str = "gpt-4o-mini", **kwargs) -> AsyncGenerator[str, None]:
        """
        Stream chat completion responses

        Args:
            messages: List of message dictionaries
            model: Model name to use
            **kwargs: Additional parameters for the request
        """
        try:
            stream = await self.async_client.chat.completions.create(
                model=model,
                messages=messages,
                stream=True,
                **kwargs
            )

            async for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            print(f"❌ Streaming failed: {e}")
            yield f"Error: {e}"

def print_separator(title: str):
    """Print a formatted separator for demo sections"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

async def demo_basic_chat(client: LiteLLMClient):
    """Demonstrate basic chat completion"""
    print_separator("Basic Chat Completion")

    messages = [
        {"role": "user", "content": "Explain what LiteLLM is in one paragraph."}
    ]

    print("🔄 Sending request to gpt-4o-mini...")
    response = await client.chat_completion_async(messages, model="gpt-4o-mini")

    if response:
        print(f"🤖 Response: {response}")
    else:
        print("❌ Failed to get response")

async def demo_model_comparison(client: LiteLLMClient):
    """Demonstrate using different models for the same prompt"""
    print_separator("Model Comparison")

    models = ["gpt-4o-mini", "claude-3-5-haiku"]
    prompt = "Write a haiku about artificial intelligence."

    messages = [{"role": "user", "content": prompt}]

    for model in models:
        print(f"🔄 Requesting from {model}...")
        response = await client.chat_completion_async(messages, model=model)

        if response:
            print(f"🤖 {model}:\n{response}\n")
        else:
            print(f"❌ {model}: Failed to get response\n")

async def demo_streaming(client: LiteLLMClient):
    """Demonstrate streaming responses"""
    print_separator("Streaming Response")

    messages = [
        {"role": "user", "content": "Tell me a short story about a robot learning to paint. Stream the response word by word."}
    ]

    print("🔄 Streaming response from gpt-4o...")
    print("🤖 Response: ", end="", flush=True)

    async for chunk in client.chat_completion_stream(messages, model="gpt-4o"):
        print(chunk, end="", flush=True)

    print("\n")  # New line after streaming

async def demo_error_handling(client: LiteLLMClient):
    """Demonstrate error handling and fallbacks"""
    print_separator("Error Handling & Fallbacks")

    # Try with an invalid model first
    messages = [{"role": "user", "content": "Hello, can you hear me?"}]

    print("🔄 Trying invalid model 'invalid-model-name'...")
    response = await client.chat_completion_async(messages, model="invalid-model-name")

    if not response:
        print("❌ Invalid model failed as expected")
        print("🔄 Falling back to gpt-4o-mini...")
        response = await client.chat_completion_async(messages, model="gpt-4o-mini")

        if response:
            print(f"✅ Fallback successful: {response}")

async def demo_custom_parameters(client: LiteLLMClient):
    """Demonstrate using custom parameters"""
    print_separator("Custom Parameters")

    messages = [
        {"role": "user", "content": "Generate 3 creative business ideas for a tech startup."}
    ]

    # High creativity
    print("🔄 High creativity (temperature=1.0)...")
    response_creative = await client.chat_completion_async(
        messages,
        model="gpt-4o-mini",
        temperature=1.0,
        max_tokens=150
    )

    # Low creativity
    print("🔄 Low creativity (temperature=0.1)...")
    response_conservative = await client.chat_completion_async(
        messages,
        model="gpt-4o-mini",
        temperature=0.1,
        max_tokens=150
    )

    if response_creative:
        print(f"🎨 Creative Response:\n{response_creative}\n")

    if response_conservative:
        print(f"🎯 Conservative Response:\n{response_conservative}\n")

async def demo_conversation_context(client: LiteLLMClient):
    """Demonstrate maintaining conversation context"""
    print_separator("Conversation Context")

    # Start a conversation
    conversation = [
        {"role": "user", "content": "My name is supra and I'm a software engineer."}
    ]

    print("🔄 Initial message...")
    response1 = await client.chat_completion_async(conversation, model="gpt-4o-mini")

    if response1:
        print(f"🤖 Bot: {response1}")
        conversation.append({"role": "assistant", "content": response1})

        # Continue conversation
        conversation.append({"role": "user", "content": "What's my name and profession?"})

        print("\n🔄 Follow-up question...")
        response2 = await client.chat_completion_async(conversation, model="gpt-4o-mini")

        if response2:
            print(f"🤖 Bot: {response2}")

async def main():
    """Main demo function"""
    print("🚀 LiteLLM Proxy Sample Application")
    print("===================================")

    # Initialize client
    proxy_url = os.getenv('LITELLM_PROXY_URL', 'http://localhost:4000')
    client = LiteLLMClient(proxy_url=proxy_url)

    # Check proxy health
    print(f"🔍 Checking proxy health at {proxy_url}...")
    if not await client.check_proxy_health():
        print("❌ Proxy is not available. Make sure it's running with:")
        print("   docker-compose up -d")
        return

    print("✅ Proxy is healthy!")

    # List available models
    print("📋 Fetching available models...")
    models = await client.list_models()
    if models:
        print(f"✅ Available models: {', '.join(models)}")
    else:
        print("⚠️  Could not fetch models, continuing with defaults...")

    try:
        # Run all demos
        await demo_basic_chat(client)
        await demo_model_comparison(client)
        await demo_streaming(client)
        await demo_error_handling(client)
        await demo_custom_parameters(client)
        await demo_conversation_context(client)

        print_separator("Demo Complete")
        print("✅ All demos completed successfully!")
        print("💡 Try modifying the examples above to explore more features.")

    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")

if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())