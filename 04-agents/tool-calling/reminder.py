import json

from anthropic import Anthropic
from anthropic.types import Message, MessageParam, ToolResultBlockParam
from tools.add_duration import add_duration_to_datetime, add_duration_to_datetime_schema
from tools.current_datetime import get_current_datetime, get_current_datetime_schema
from tools.set_reminder import set_reminder, set_reminder_schema

from messaging import add_assistant_message, add_user_message, chat, text_from_message

client = Anthropic()


def run_tool(tool_name: str, tool_input):
    if tool_name == "get_current_datetime":
        return get_current_datetime(**tool_input)
    elif tool_name == "add_duration_to_datetime":
        return add_duration_to_datetime(**tool_input)
    elif tool_name == "set_reminder":
        return set_reminder(**tool_input)


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
            tools=[
                get_current_datetime_schema,
                add_duration_to_datetime_schema,
                set_reminder_schema,
            ],
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
