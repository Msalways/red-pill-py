"""LLM provider wrapper for LangChain chat models."""

from typing import Any, Type

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig


class LLMProvider:
    """Wrapper for LangChain chat models.

    This is the interface used internally by Redpill agents.
    Any LangChain-compatible chat model can be wrapped with this.
    """

    def __init__(
        self,
        llm: BaseChatModel,
        temperature: float = 0.7,
        max_tokens: int = 4000,
    ) -> None:
        """Initialize with a LangChain chat model.

        Args:
            llm: Any LangChain-compatible chat model
            temperature: Default temperature for generation
            max_tokens: Default max tokens for generation
        """
        self._llm = llm
        self._temperature = temperature
        self._max_tokens = max_tokens

    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4000,
    ) -> str:
        """Generate a response from the LLM."""
        messages = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=prompt))

        config: RunnableConfig = {
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        response = self._llm.invoke(messages, config=config)

        content = response.content
        if isinstance(content, str):
            return content
        return str(content)

    def generate_json(
        self,
        prompt: str,
        response_schema: Type[Any],
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4000,
    ) -> Any:
        """Generate a JSON response with schema validation."""
        from langchain_core.output_parsers import JsonOutputParser

        messages = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))

        parser = JsonOutputParser(pydantic_object=response_schema)

        format_instructions = parser.get_format_instructions()
        full_prompt = f"{prompt}\n\n{format_instructions}"
        messages.append(HumanMessage(content=full_prompt))

        config: RunnableConfig = {
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        response = self._llm.invoke(messages, config=config)

        content = response.content
        if isinstance(content, str):
            parsed = parser.parse(content)
        else:
            parsed = parser.parse(str(content))

        return response_schema(**parsed)


def create_llm_provider(llm: BaseChatModel, **kwargs: Any) -> LLMProvider:
    """Create an LLMProvider from a LangChain chat model.
    
    Args:
        llm: Any LangChain-compatible chat model
        **kwargs: Additional args passed to LLMProvider
        
    Returns:
        LLMProvider instance
    """
    return LLMProvider(llm=llm, **kwargs)
