import json
from typing import Callable

from anthropic import Anthropic
from anthropic.types import (
    Message,
    MessageParam,
    ToolChoiceParam,
    ToolResultBlockParam,
    ToolUnionParam,
)

from api_config import dev_config

client = Anthropic()


def add_user_message(
    messages: list[MessageParam], message: Message | str | list[ToolResultBlockParam]
) -> list[MessageParam]:
    """Append a user turn to messages and return the list."""
    user_message: MessageParam = {
        "role": "user",
        "content": message.content if isinstance(message, Message) else message,
    }
    messages.append(user_message)
    return messages


def add_assistant_message(
    messages: list[MessageParam], message: Message | str
) -> list[MessageParam]:
    """Append an assistant turn to messages and return the list."""
    assistant_message: MessageParam = {
        "role": "assistant",
        "content": message.content if isinstance(message, Message) else message,
    }
    messages.append(assistant_message)
    return messages


def chat(
    messages: list[MessageParam],
    max_tokens: int = dev_config.max_tokens,
    system: str | None = None,
    temperature: float = 1.0,
    stop_sequences: list[str] | None = None,
    tools: list[ToolUnionParam] | None = None,
    tool_choice: ToolChoiceParam | None = None,
) -> Message:
    """Send messages to the model and return the response."""
    params = {
        "model": dev_config.model,
        "max_tokens": max_tokens,
        "messages": messages,
        "temperature": temperature,
    }

    if system:
        params["system"] = system
    if stop_sequences:
        params["stop_sequences"] = stop_sequences
    if tools:
        params["tools"] = tools
    if tool_choice:
        params["tool_choice"] = tool_choice

    message = client.messages.create(**params)
    dev_config.record_token_usage(message)
    return message


def text_from_message(message: Message) -> str:
    """Extract and join all text blocks from a message."""
    return "\n".join([block.text for block in message.content if block.type == "text"])


def run_tools(
    message: Message,
    tool_registry: dict[str, Callable],
) -> list[ToolResultBlockParam]:
    """Execute all tool_use blocks in message and return their results.

    Each tool is dispatched as `tool_registry[name](**input)`. Exceptions are
    caught and returned as error results rather than raised.
    """
    tool_results: list[ToolResultBlockParam] = []

    for block in message.content:
        if block.type != "tool_use":
            continue

        tool_result: ToolResultBlockParam = {
            "type": "tool_result",
            "tool_use_id": block.id,
            "content": "",
            "is_error": False,
        }

        try:
            tool_result["content"] = json.dumps(
                tool_registry[block.name](**block.input)
            )
        except Exception as e:
            tool_result["content"] = f"Error: {e}"
            tool_result["is_error"] = True

        tool_results.append(tool_result)

    return tool_results


def run_agent_loop(
    messages: list[MessageParam],
    tools: list[ToolUnionParam],
    tool_registry: dict[str, Callable],
    system: str | None = None,
    tool_choice: ToolChoiceParam | None = None,
) -> list[MessageParam]:
    """Run a chat+tool loop until the model stops requesting tool use.

    Mutates and returns messages with the full conversation history appended.
    """
    while True:
        message = chat(messages, tools=tools, system=system, tool_choice=tool_choice)
        add_assistant_message(messages, message)

        if message.stop_reason != "tool_use":
            break

        add_user_message(messages, run_tools(message, tool_registry))

    return messages
