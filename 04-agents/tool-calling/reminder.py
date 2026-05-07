from tools import tool_registry, tool_schemas

from messaging import add_user_message, run_agent_loop

messages = add_user_message(
    [],
    "Using the batch tool, set a reminder for my doctor's appointment. It's 177 days from today.",
)

run_agent_loop(messages, tool_schemas, tool_registry, max_tokens=1000)
