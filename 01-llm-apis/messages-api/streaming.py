from anthropic import Anthropic
from anthropic.types import RawContentBlockDeltaEvent

from api_config import dev_config

client = Anthropic()

stream = client.messages.create(
    model=dev_config.model,
    max_tokens=dev_config.max_tokens,
    stream=True,
    messages=[
        {
            "role": "user",
            "content": "Hello, Claudette.",
        }
    ],
)

response = ""

for event in stream:
    print(event, "\n")

    if isinstance(event, RawContentBlockDeltaEvent):
        response += event.delta.text

print(response)
