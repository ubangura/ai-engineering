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
    messages: list[MessageParam], system: str | None = None, temperature: float = 1.0
) -> str:
    params = {
        "model": dev_config.model,
        "max_tokens": dev_config.max_tokens,
        "messages": messages,
        "temperature": temperature,
    }

    if system:
        params["system"] = system

    message = client.messages.create(**params)
    return message.content[0].text
