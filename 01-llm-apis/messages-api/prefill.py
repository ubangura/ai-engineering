from anthropic import Anthropic

from api_config import dev_config

client = Anthropic()

message = client.messages.create(
    model=dev_config.model,
    max_tokens=2,
    messages=[
        {"role": "user", "content": "What is English for the word كتاب"},
        {"role": "assistant", "content": 'كتاب in English is "'},
    ],
)

print(message.content[0].text)
