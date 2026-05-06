import atexit
import os
from datetime import timedelta
from typing import ClassVar

from anthropic.types import Message
from dotenv import load_dotenv

load_dotenv()


HAIKU = "claude-haiku-4-5-20251001"
SONNET = "claude-sonnet-4-6"
OPUS = "claude-opus-4-7"

# Per-model pricing ($ per 1M tokens)
_PRICING: dict[str, dict[str, float]] = {
    HAIKU: {"input": 1.00, "output": 5.00},
    SONNET: {"input": 3.00, "output": 15.00},
    OPUS: {"input": 5.00, "output": 25.00},
}


class APIConfig:
    retries_on_failure: ClassVar[int] = 3
    retry_delay: ClassVar[timedelta] = timedelta(seconds=10)

    def __init__(
        self,
        api_key: str,
        model: str = HAIKU,
        max_tokens: int = 100,
        timeout: timedelta = timedelta(seconds=10),
    ):
        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens
        self.timeout = timeout
        self._input_tokens_used: int = 0
        self._output_tokens_used: int = 0
        atexit.register(self._print_usage_summary)

    def record_token_usage(self, response: Message) -> None:
        self._input_tokens_used += response.usage.input_tokens
        self._output_tokens_used += response.usage.output_tokens

    def _print_usage_summary(self) -> None:
        if self._input_tokens_used == 0 and self._output_tokens_used == 0:
            return
        pricing = _PRICING.get(self.model, {"input": 0, "output": 0})
        input_cost = self._input_tokens_used / 1_000_000 * pricing["input"]
        output_cost = self._output_tokens_used / 1_000_000 * pricing["output"]
        total_cost = input_cost + output_cost

        print(
            f"\n--- API Usage Summary ({self.model}) ---\n"
            f"  Input tokens:  {self._input_tokens_used:,}  (${input_cost:.4f})\n"
            f"  Output tokens: {self._output_tokens_used:,}  (${output_cost:.4f})\n"
            f"  Total cost:    ${total_cost:.4f}\n"
        )


# ---------------------------------------------------------------------
# Configurations
# ---------------------------------------------------------------------

dev_config = APIConfig(
    api_key=os.environ.get("ANTHROPIC_API_KEY") or "",
    model=HAIKU,
    max_tokens=500,
)

prod_config = APIConfig(
    api_key=os.environ.get("ANTHROPIC_API_KEY") or "",
    model=SONNET,
    max_tokens=1000,
)
