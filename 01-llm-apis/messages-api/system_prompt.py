from anthropic import Anthropic

from messaging import add_user_message, chat, text_from_message

client = Anthropic()

system = """
You are a patient math tutor.
Do not directly answer a student's questions.
Guide them to a solution step-by-step.
"""

messages = []
add_user_message(messages, "How do I solve 5x + 3 = 2 for x?")
message = chat(messages, system=system)
print(text_from_message(message))
