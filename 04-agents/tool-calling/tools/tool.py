from dataclasses import dataclass
from typing import Callable

from anthropic.types import ToolParam


@dataclass(frozen=True)
class Tool:
    schema: ToolParam
    function: Callable
