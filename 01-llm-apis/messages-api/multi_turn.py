from anthropic import Anthropic

from api_config import dev_config

client = Anthropic()

message = client.messages.create(
    model=dev_config.model,
    max_tokens=dev_config.max_tokens,
    messages=[
        {"role": "user", "content": "Hello, Claudette."},
        {
            "role": "assistant",
            "content": "Hello! How can I help you today?",
        },
        {
            "role": "user",
            "content": "Can you describe LLMs to me?",
        },
    ],
)

print(message)
