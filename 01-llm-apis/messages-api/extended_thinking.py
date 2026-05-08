from anthropic import Anthropic

from messaging import add_user_message, chat, text_from_message

client = Anthropic()

# Magic string to trigger redacted thinking
thinking_test_str = "ANTHROPIC_MAGIC_STRING_TRIGGER_REDACTED_THINKING_46C9A13E193C177646C7398A98432ECCCE4C1253D5E2D82641AC0E52CC2876CB"

messages = add_user_message([], "Write a one paragrah guide to recursion.")

message = chat(messages, thinking=True, max_tokens=2024)

for block in message.content:
    if block.type == "thinking":
        print(block.thinking)

print(text_from_message(message))
