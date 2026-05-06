from typing import Callable

from anthropic.types import ToolUnionParam

from tools.add_duration import add_duration_to_datetime, add_duration_to_datetime_schema
from tools.current_datetime import get_current_datetime, get_current_datetime_schema
from tools.set_reminder import set_reminder, set_reminder_schema

tool_registry: dict[str, Callable] = {
    "get_current_datetime": get_current_datetime,
    "add_duration_to_datetime": add_duration_to_datetime,
    "set_reminder": set_reminder,
}

tool_schemas: list[ToolUnionParam] = [
    get_current_datetime_schema,
    add_duration_to_datetime_schema,
    set_reminder_schema,
]
