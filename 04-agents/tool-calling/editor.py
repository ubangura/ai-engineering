from tools.text_editor import tool_registry, tool_schema

from messaging import add_user_message, run_agent_loop

messages = add_user_message(
    [],
    """Open the ./edit.py file and write out a function to calculate PI to the 5th digit.
    Then create a ./test.py file to test your implementation.""",
)

run_agent_loop(messages, [tool_schema], tool_registry)
