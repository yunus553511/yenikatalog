"""
Groq API HTTP Client
"""
import aiohttp
import asyncio
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class GroqAPIError(Exception):
    """Groq API genel hatası"""
    pass


class GroqRateLimitError(GroqAPIError):
    """Rate limit hatası (429)"""
    pass


class GroqTimeoutError(GroqAPIError):
    """Timeout hatası"""
    pass


class GroqClient:
    """Groq API HTTP client"""
    
    def __init__(self, api_key: str, base_url: str = "https://api.groq.com/openai/v1"):
        """
        Initialize Groq client
        
        Args:
            api_key: Groq API key
            base_url: Groq API base URL
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.session: Optional[aiohttp.ClientSession] = None
        
        logger.info(f"GroqClient initialized with base_url: {self.base_url}")
    
    async def __aenter__(self):
        """Context manager entry"""
        await self._ensure_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        await self.close()
    
    async def _ensure_session(self):
        """Ensure aiohttp session exists"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
            )
            logger.debug("Created new aiohttp session")
    
    async def chat_completion(
        self,
        messages: List[Dict],
        model: str = "llama-3.3-70b-versatile",
        tools: Optional[List[Dict]] = None,
        tool_choice: str = "auto",
        temperature: float = 0.7,
        max_tokens: int = 1000,
        timeout: int = 10
    ) -> Dict:
        """
        Chat completion API call with function calling support
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model name
            tools: Tool/function definitions (Groq format)
            tool_choice: "auto", "none", or specific tool name
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
            timeout: Request timeout in seconds
            
        Returns:
            {
                "message": str or None,  # None if tool_calls present
                "tool_calls": List[Dict] or None,  # Tool calls if LLM wants to call functions
                "tokens_used": int,
                "model": str
            }
            
        Raises:
            GroqRateLimitError: Rate limit exceeded (429)
            GroqTimeoutError: Request timeout
            GroqAPIError: Other API errors
        """
        await self._ensure_session()
        
        url = f"{self.base_url}/chat/completions"
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        # Add tools if provided
        if tools:
            payload["tools"] = tools
            payload["parallel_tool_calls"] = False  # Disable parallel calls to avoid format issues
            # Only add tool_choice if it's not "auto" (Groq default)
            if tool_choice != "auto":
                payload["tool_choice"] = tool_choice
        
        logger.debug(f"Sending request to Groq API: model={model}, messages={len(messages)}, tools={len(tools) if tools else 0}")
        
        try:
            async with self.session.post(
                url,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as response:
                
                # Rate limit check
                if response.status == 429:
                    error_text = await response.text()
                    logger.warning(f"Rate limit exceeded: {error_text}")
                    raise GroqRateLimitError("Rate limit exceeded (429)")
                
                # Other HTTP errors
                if response.status >= 400:
                    error_text = await response.text()
                    logger.error(f"Groq API error {response.status}: {error_text}")
                    raise GroqAPIError(f"API error {response.status}: {error_text}")
                
                # Parse response
                data = await response.json()
                
                # Extract message from response
                message_obj = data["choices"][0]["message"]
                
                # Check if LLM wants to call tools
                tool_calls = message_obj.get("tool_calls")
                message_content = message_obj.get("content")
                
                tokens_used = data.get("usage", {}).get("total_tokens", 0)
                model_used = data.get("model", model)
                
                if tool_calls:
                    logger.info(f"Groq API success with tool calls: {len(tool_calls)} calls, tokens={tokens_used}")
                else:
                    logger.info(f"Groq API success: tokens={tokens_used}, model={model_used}")
                
                return {
                    "message": message_content,
                    "tool_calls": tool_calls,
                    "tokens_used": tokens_used,
                    "model": model_used
                }
                
        except aiohttp.ClientError as e:
            logger.error(f"Network error: {e}")
            raise GroqTimeoutError(f"Network error: {e}")
        
        except asyncio.TimeoutError:
            logger.error(f"Request timeout after {timeout}s")
            raise GroqTimeoutError(f"Request timeout after {timeout}s")
    
    async def close(self):
        """Close aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()
            logger.debug("Closed aiohttp session")
