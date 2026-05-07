from anthropic.types import ToolParam

from messaging import add_user_message, chat

web_search_schema: ToolParam = {
    "type": "web_search_20250305",
    "name": "web_search",
    "max_uses": 5,
    "allowed_domains": ["nih.gov"],
}

messages = add_user_message([], "What's the best exercise for gaining leg muscle?")

message = chat(messages, tools=[web_search_schema])
message
