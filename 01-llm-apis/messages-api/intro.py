from anthropic import Anthropic

from api_config import dev_config

client = Anthropic()

message = client.messages.create(
    model=dev_config.model,
    max_tokens=dev_config.max_tokens,
    messages=[{"role": "user", "content": "Good morning, Claudette."}],
)
print(message.content[0].text)
