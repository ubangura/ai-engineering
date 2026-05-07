import json

from anthropic.types import Message, MessageParam, ToolResultBlockParam
from tools.text_editor import tool_registry, tool_schemas

from messaging import add_assistant_message, add_user_message, chat, text_from_message


def run_tool(tool_name, tool_input):
    handler = tool_registry.get(tool_name)
    if handler is None:
        raise ValueError(f"Unknown tool name: {tool_name}")
    return handler(tool_input)


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
            tools=tool_schemas,
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
    """Open the ./edit.py file and write out a function to calculate PI to the 5th digit.
    Then create a ./test.py file to test your implementation.""",
)

run_conversation(messages)
