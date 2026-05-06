from anthropic import Anthropic
from anthropic.types import Message, MessageParam, ToolResultBlockParam, ToolUnionParam

from api_config import dev_config

client = Anthropic()


def add_user_message(
    messages: list[MessageParam], message: Message | str | list[ToolResultBlockParam]
) -> list[MessageParam]:
    user_message: MessageParam = {
        "role": "user",
        "content": message.content if isinstance(message, Message) else message,
    }
    messages.append(user_message)
    return messages


def add_assistant_message(
    messages: list[MessageParam], message: Message | str
) -> list[MessageParam]:
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
) -> Message:
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

    message = client.messages.create(**params)
    dev_config.record_token_usage(message)
    return message


def text_from_message(message: Message) -> str:
    return "\n".join([block.text for block in message.content if block.type == "text"])
