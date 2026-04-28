from enum import Enum

from anthropic import Anthropic
from pydantic import BaseModel, Field

from api_config import dev_config

client = Anthropic()


class TicketCategory(str, Enum):
    """Categories for incoming tickets."""

    GENERAL = "general"
    ORDER = "order"
    RETURN = "return"
    BILLING = "billing"


class TicketResolution(BaseModel):
    class Step(BaseModel):
        description: str = Field(description="Description of the step taken.")
        action: str = Field(description="Action taken to resolve the issue.")

    category: TicketCategory = Field(
        description="The category of the ticket", default=TicketCategory.GENERAL
    )
    steps: list[Step]
    final_resolution: str = Field(description="Final message sent to the customer")
    confidence: float = Field(description="Confidence in the resolution", ge=0, le=1)


message = client.messages.parse(
    model=dev_config.model,
    max_tokens=1000,
    messages=[
        {
            "role": "assistant",
            "content": """
            You are a customer care assistant. You will be provided with a customer inquiry,
            and your goal is to respond with a structured solution, including the steps taken to resolve the issue and the final resolution.
            For each step, provide a description and the action taken.
            """,
        },
        {
            "role": "user",
            "content": """
            Hi, I'm having trouble with my recent order. I received the wrong item and need to return it for a refund. 
            Can you help me with the return process and let me know when I can expect my refund?
            """,
        },
    ],
    output_format=TicketResolution,
)

resolution = message.parsed_output

if resolution:
    for step in resolution.steps:
        print(f"Step: {step.description}")
        print(f"Action: {step.action}\n")
    print(resolution.final_resolution)
