from anthropic import Anthropic

from api_config import dev_config
from messaging import add_user_message

client = Anthropic()

messages = add_user_message([], "Generate placeholder text for a web mockup.")

with client.messages.stream(
    model=dev_config.model, max_tokens=1000, messages=messages
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)
    print()

stream.get_final_message()
