from anthropic import Anthropic
from anthropic.types import MessageParam

from api_config import dev_config

client = Anthropic()


def add_user_message(messages: list[MessageParam], text: str) -> list[MessageParam]:
    user_message: MessageParam = {"role": "user", "content": text}
    messages.append(user_message)
    return messages


def add_assistant_message(
    messages: list[MessageParam], text: str
) -> list[MessageParam]:
    assistant_message: MessageParam = {"role": "assistant", "content": text}
    messages.append(assistant_message)
    return messages


def chat(
    messages: list[MessageParam],
    max_tokens: int = dev_config.max_tokens,
    system: str | None = None,
    temperature: float = 1.0,
    stop_sequences: list[str] | None = None,
) -> str:
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

    message = client.messages.create(**params)
    dev_config.record_token_usage(message)
    return message.content[0].text
