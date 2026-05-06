from messaging import add_assistant_message, add_user_message, chat, text_from_message

messages = add_user_message(
    [],
    "What are the available datatypes in JSON? Explain in one sentence with an example.",
)
add_assistant_message(messages, "```json")

print(text_from_message(chat(messages, max_tokens=100)))

print(text_from_message(chat(messages, max_tokens=100, stop_sequences=["```"])))
