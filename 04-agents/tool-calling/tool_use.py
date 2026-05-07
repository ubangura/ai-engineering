import requests
from anthropic.types import MessageParam, ToolUnionParam

from messaging import add_assistant_message, add_user_message, chat


def get_weather() -> str:
    url = "https://api.open-meteo.com/v1/forecast?latitude=38.8951&longitude=-77.0364&current=temperature_2m&temperature_unit=fahrenheit"
    response = requests.get(url)
    data = response.json()

    return (
        f"{data['current']['temperature_2m']}{data['current_units']['temperature_2m']}"
    )


messages: list[MessageParam] = [
    {"role": "user", "content": "What's the weather like today?"}
]

tools: list[ToolUnionParam] = [
    {
        "name": "get_weather",
        "description": "Get the current weather for the user location",
        "input_schema": {
            "type": "object",
            "properties": {},
        },
    }
]

response = chat(messages, tools=tools)

if response.stop_reason != "tool_use":
    print(response.content[0].text)
    exit()

tool_use = next(block for block in response.content if block.type == "tool_use")

add_assistant_message(messages, response)
add_user_message(messages, [{"type": "tool_result", "tool_use_id": tool_use.id, "content": get_weather()}])

final_response = chat(messages, tools=tools)

print(final_response.content[0].text)
