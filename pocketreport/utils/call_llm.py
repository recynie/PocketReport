"""
Utility function for calling LLM APIs (OpenAI-compatible).
"""
import os
import json
from typing import Optional, Dict, Any
import requests


def call_llm(
    system_prompt: str,
    user_prompt: str,
    json_mode: bool = False,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    temperature: float = 0.1,
    max_tokens: int = 4000
) -> str:
    """
    Call an OpenAI-compatible LLM API.
    
    Args:
        system_prompt: System prompt for the LLM
        user_prompt: User prompt for the LLM
        json_mode: Whether to request JSON output
        model: Model name (defaults to env var LLM_MODEL or "gpt-4o")
        api_key: API key (defaults to env var LLM_API_KEY)
        base_url: API base URL (defaults to env var LLM_BASE_URL or OpenAI)
        temperature: Sampling temperature
        max_tokens: Maximum tokens to generate
        
    Returns:
        LLM response as string (or parsed dict if json_mode=True and valid JSON)
    """
    # Get configuration from environment variables if not provided
    model = model or os.getenv("LLM_MODEL", "gpt-4o")
    api_key = api_key or os.getenv("LLM_API_KEY")
    base_url = base_url or os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
    
    if not api_key:
        raise ValueError("LLM_API_KEY environment variable must be set or api_key must be provided")
    
    # Prepare headers
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    # Prepare messages
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    # Prepare request body
    body: Dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    
    if json_mode:
        body["response_format"] = {"type": "json_object"}
    
    # Make the API call
    try:
        response = requests.post(
            f"{base_url}/chat/completions",
            headers=headers,
            json=body,
            timeout=60
        )
        response.raise_for_status()
        
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        
        # Parse JSON if requested
        if json_mode:
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                # If JSON parsing fails, return the raw content
                # This allows the caller to handle parsing errors
                return content
        
        return content
        
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"LLM API call failed: {e}")


def call_llm_with_retry(
    system_prompt: str,
    user_prompt: str,
    json_mode: bool = False,
    max_retries: int = 3,
    **kwargs
) -> str:
    """
    Call LLM with retry logic.
    
    Args:
        system_prompt: System prompt for the LLM
        user_prompt: User prompt for the LLM
        json_mode: Whether to request JSON output
        max_retries: Maximum number of retry attempts
        **kwargs: Additional arguments passed to call_llm
        
    Returns:
        LLM response
    """
    for attempt in range(max_retries):
        try:
            return call_llm(system_prompt, user_prompt, json_mode, **kwargs)
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            # Wait before retry (exponential backoff)
            import time
            time.sleep(2 ** attempt)
    
    # This should never be reached
    raise RuntimeError("Failed to call LLM after retries")


if __name__ == "__main__":
    # Test the LLM call with a simple prompt
    test_system = "You are a helpful assistant."
    test_user = "Say 'Hello, world!' in a creative way."
    
    print("Testing LLM call...")
    try:
        response = call_llm(test_system, test_user)
        print(f"Response: {response}")
    except Exception as e:
        print(f"Error: {e}")
        print("Note: Set LLM_API_KEY environment variable to test")