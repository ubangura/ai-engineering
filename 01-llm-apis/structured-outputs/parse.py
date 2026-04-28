from anthropic import Anthropic
from pydantic import BaseModel, EmailStr

from api_config import dev_config

client = Anthropic()


class ContactInfo(BaseModel):
    name: str
    email: EmailStr
    plan_interest: str


message = client.messages.parse(
    model=dev_config.model,
    max_tokens=dev_config.max_tokens,
    messages=[
        {
            "role": "user",
            "content": "Extract contact info: John Smith, john@example.com, interested in the Pro plan",
        },
    ],
    output_format=ContactInfo,
)

contact = message.parsed_output
print(contact)
