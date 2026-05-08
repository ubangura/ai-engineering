import base64

from messaging import add_user_message, chat, text_from_message

with open("prompting-claude.pdf", "rb") as f:
    file_bytes = base64.standard_b64encode(f.read()).decode("utf-8")

messages = add_user_message(
    [],
    [
        {
            "type": "document",
            "source": {
                "type": "base64",
                "media_type": "application/pdf",
                "data": file_bytes,
            },
            "title": "prompting-claude.pdf",
            "citations": {"enabled": True},
        },
        {
            "type": "text",
            "text": "What is one of the most  reliable ways to steer Claude's output format, tone, and structure",
        },
    ],
)

message = chat(messages)
print(text_from_message(message))
print(message.model_dump_json(indent=2))
