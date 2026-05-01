from messaging import add_assistant_message, add_user_message, chat

messages = add_user_message(
    [],
    "What are the available datatypes in JSON? Explain in one sentence with an example.",
)
add_assistant_message(messages, "```json")

print(chat(messages, max_tokens=100))

print(chat(messages, max_tokens=100, stop_sequences=["```"]))
