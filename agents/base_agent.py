from typing import List, Dict, Any, Optional, Callable
import json
from abc import ABC, abstractmethod
import anthropic
import openai
import requests
from config import settings


class BaseLLMClient(ABC):
    """Base class for LLM clients."""

    @abstractmethod
    def create_message(
        self,
        messages: List[Dict],
        tools: Optional[List[Dict]] = None,
        max_tokens: int = 4096
    ) -> Dict:
        """Create a message with the LLM."""
        pass


class AnthropicClient(BaseLLMClient):
    """Anthropic Claude client."""

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self.model = settings.anthropic_model

    def create_message(
        self,
        messages: List[Dict],
        tools: Optional[List[Dict]] = None,
        max_tokens: int = 4096
    ) -> Dict:
        """Create a message with Claude."""
        kwargs = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": messages
        }

        if tools:
            kwargs["tools"] = tools

        response = self.client.messages.create(**kwargs)

        return {
            "content": response.content,
            "stop_reason": response.stop_reason,
            "usage": {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens
            }
        }


class OpenAIClient(BaseLLMClient):
    """OpenAI GPT client."""

    def __init__(self):
        self.client = openai.OpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model

    def create_message(
        self,
        messages: List[Dict],
        tools: Optional[List[Dict]] = None,
        max_tokens: int = 4096
    ) -> Dict:
        """Create a message with GPT."""
        kwargs = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": messages
        }

        if tools:
            # Convert to OpenAI function format
            kwargs["tools"] = [
                {
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "description": tool["description"],
                        "parameters": tool["input_schema"]
                    }
                }
                for tool in tools
            ]

        response = self.client.chat.completions.create(**kwargs)

        # Convert to standardized format
        message = response.choices[0].message

        content = []
        if message.content:
            content.append({"type": "text", "text": message.content})

        if message.tool_calls:
            for tool_call in message.tool_calls:
                content.append({
                    "type": "tool_use",
                    "id": tool_call.id,
                    "name": tool_call.function.name,
                    "input": json.loads(tool_call.function.arguments)
                })

        return {
            "content": content,
            "stop_reason": "tool_use" if message.tool_calls else "end_turn",
            "usage": {
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens
            }
        }


class OllamaClient(BaseLLMClient):
    """Ollama local LLM client."""

    def __init__(self):
        self.base_url = settings.ollama_base_url
        self.model = settings.ollama_model

    def create_message(
        self,
        messages: List[Dict],
        tools: Optional[List[Dict]] = None,
        max_tokens: int = 4096
    ) -> Dict:
        """Create a message with Ollama."""
        # Ollama uses a simpler chat API
        # Convert messages to Ollama format
        ollama_messages = []
        for msg in messages:
            role = msg.get("role")
            content = msg.get("content")

            # Handle text content
            if isinstance(content, str):
                ollama_messages.append({"role": role, "content": content})
            elif isinstance(content, list):
                # Extract text from content blocks
                text_parts = [block.get("text", "") for block in content if block.get("type") == "text"]
                ollama_messages.append({"role": role, "content": " ".join(text_parts)})

        response = requests.post(
            f"{self.base_url}/api/chat",
            json={
                "model": self.model,
                "messages": ollama_messages,
                "stream": False
            }
        )

        if response.status_code != 200:
            raise Exception(f"Ollama API error: {response.status_code} - {response.text}")

        result = response.json()
        message_content = result.get("message", {}).get("content", "")

        return {
            "content": [{"type": "text", "text": message_content}],
            "stop_reason": "end_turn",
            "usage": {
                "input_tokens": 0,  # Ollama doesn't provide token counts
                "output_tokens": 0
            }
        }


class BaseAgent:
    """
    Base agent class with tool calling capabilities.
    Supports multiple LLM providers (Anthropic, OpenAI, Gemini, Ollama).
    """

    def __init__(self, system_prompt: str, tools: Optional[List[Dict]] = None):
        """
        Initialize the agent.

        Args:
            system_prompt: System prompt defining agent behavior
            tools: List of tool definitions the agent can use
        """
        self.system_prompt = system_prompt
        self.tools = tools or []
        self.conversation_history: List[Dict] = []
        self.tool_functions: Dict[str, Callable] = {}

        # Initialize LLM client based on settings
        self.llm_client = self._init_llm_client()

    def _init_llm_client(self) -> BaseLLMClient:
        """Initialize the appropriate LLM client."""
        if settings.llm_provider == "anthropic":
            return AnthropicClient()
        elif settings.llm_provider == "openai":
            return OpenAIClient()
        elif settings.llm_provider == "ollama":
            return OllamaClient()
        else:
            raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}")

    def register_tool(self, name: str, function: Callable) -> None:
        """
        Register a tool function that the agent can call.

        Args:
            name: Name of the tool (must match tool definition)
            function: Callable function to execute
        """
        self.tool_functions[name] = function

    def run(self, user_message: str, max_iterations: int = 10) -> str:
        """
        Run the agent with a user message using agentic workflow.

        Args:
            user_message: User's input message
            max_iterations: Maximum number of agent iterations

        Returns:
            Final response from the agent
        """
        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })

        iteration = 0
        final_response = ""

        while iteration < max_iterations:
            iteration += 1

            # Create messages with system prompt
            messages = [{"role": "user", "content": self.system_prompt}] + self.conversation_history

            # Get response from LLM
            response = self.llm_client.create_message(
                messages=messages,
                tools=self.tools if self.tools else None
            )

            content = response["content"]
            stop_reason = response["stop_reason"]

            # Add assistant response to history
            self.conversation_history.append({
                "role": "assistant",
                "content": content
            })

            # Check if we need to execute tools
            if stop_reason == "tool_use":
                tool_results = []

                for block in content:
                    if isinstance(block, dict) and block.get("type") == "tool_use":
                        tool_name = block["name"]
                        tool_input = block["input"]
                        tool_id = block["id"]

                        # Execute the tool
                        if tool_name in self.tool_functions:
                            try:
                                result = self.tool_functions[tool_name](**tool_input)
                                tool_results.append({
                                    "type": "tool_result",
                                    "tool_use_id": tool_id,
                                    "content": json.dumps(result)
                                })
                            except Exception as e:
                                tool_results.append({
                                    "type": "tool_result",
                                    "tool_use_id": tool_id,
                                    "content": f"Error: {str(e)}",
                                    "is_error": True
                                })

                # Add tool results to conversation
                self.conversation_history.append({
                    "role": "user",
                    "content": tool_results
                })

            else:
                # Extract final text response
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        final_response = block["text"]
                    elif isinstance(block, str):
                        final_response = block

                break

        return final_response

    def reset(self) -> None:
        """Reset the conversation history."""
        self.conversation_history = []
