from anthropic import Anthropic

from api_config import dev_config

client = Anthropic()

message = client.messages.create(
    model=dev_config.model,
    max_tokens=60,
    messages=[
        {
            "role": "assistant",
            "content": """
        You're a helpful customer care assistant that classifies incoming messages and gives a response.
        Always respond in the following JSON format: {"content": <response>, "category": <classification>}
        Available categories: 'general', 'order', 'billing'
        """,
        },
        {
            "role": "user",
            "content": "Hi there, I have a question about my bill. Can you help me?",
        },
    ],
)

print(message.content[0].text)
