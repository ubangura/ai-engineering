import requests
from anthropic import Anthropic

from api_config import dev_config

client = Anthropic()


def get_weather() -> str:
    url = "https://api.open-meteo.com/v1/forecast?latitude=38.8951&longitude=-77.0364&current=temperature_2m&temperature_unit=fahrenheit"
    response = requests.get(url)
    data = response.json()

    return (
        f"{data['current']['temperature_2m']}{data['current_units']['temperature_2m']}"
    )


messages = [{"role": "user", "content": "What's the weather like today?"}]

tools = [
    {
        "name": "get_weather",
        "description": "Get the current weather for the user location",
        "input_schema": {
            "type": "object",
            "properties": {},
        },
    }
]

response = client.messages.create(
    model=dev_config.model,
    max_tokens=dev_config.max_tokens,
    messages=messages,
    tools=tools,
)

if response.stop_reason != "tool_use":
    print(response.content[0].text)
    exit()

tool_use = next(block for block in response.content if block.type == "tool_use")
result = get_weather()

messages.extend(
    [
        {"role": "assistant", "content": response.content},
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": tool_use.id,
                    "content": result,
                }
            ],
        },
    ]
)

final_response = client.messages.create(
    model=dev_config.model,
    max_tokens=dev_config.max_tokens,
    messages=messages,
    tools=tools,
)

print(final_response.content[0].text)
