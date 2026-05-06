import json

from anthropic import Anthropic
from anthropic.types import Message, MessageParam, ToolResultBlockParam
from tools import all_tools

from messaging import add_assistant_message, add_user_message, chat, text_from_message

client = Anthropic()

tool_registry = {tool.schema["name"]: tool.function for tool in all_tools}


def run_tool(tool_name: str, tool_input):
    return tool_registry[tool_name](**tool_input)


def run_tools(message: Message) -> list[ToolResultBlockParam]:
    tool_requests = [block for block in message.content if block.type == "tool_use"]
    tool_result_blocks: list[ToolResultBlockParam] = []

    for tool_request in tool_requests:
        tool_result_block: ToolResultBlockParam = {
            "type": "tool_result",
            "tool_use_id": tool_request.id,
            "content": "",
            "is_error": False,
        }

        try:
            tool_output = run_tool(tool_request.name, tool_request.input)
            tool_result_block["content"] = json.dumps(tool_output)
        except Exception as e:
            tool_result_block["content"] = f"Error: {e}"
            tool_result_block["is_error"] = True

        tool_result_blocks.append(tool_result_block)

    return tool_result_blocks


def run_conversation(messages: list[MessageParam]) -> list[MessageParam]:
    while True:
        message = chat(
            messages,
            tools=[tool.schema for tool in all_tools],
        )

        add_assistant_message(messages, message)
        print(text_from_message(message))

        if message.stop_reason != "tool_use":
            break

        tool_results = run_tools(message)
        add_user_message(messages, tool_results)

    return messages


messages = add_user_message(
    [],
    "Set a reminder for my doctor's appointment. It's 177 days after January 1, 2050.",
)

message = run_conversation(messages)
message
