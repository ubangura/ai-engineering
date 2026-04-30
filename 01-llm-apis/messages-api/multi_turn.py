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


def chat(messages: list[MessageParam]) -> str:
    message = client.messages.create(
        model=dev_config.model, max_tokens=dev_config.max_tokens, messages=messages
    )
    return message.content[0].text


messages: list[MessageParam] = []

add_user_message(messages, "Can you describe LLM's to me in one sentence?")

message = chat(messages)
add_assistant_message(messages, message)

add_user_message(messages, "Write another sentence.")

message = chat(messages)
print(message)
