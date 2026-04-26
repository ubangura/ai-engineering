import string

from pydantic import BaseModel, EmailStr, Field, HttpUrl, field_validator


class User(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    username: str = Field(min_length=3, max_length=20)
    age: int = Field(gt=0, le=120)
    email: EmailStr
    portfolio: HttpUrl | None = Field(
        default=None,
        # pattern=r"^https?://.*",
        description="URL to users online portfolio",
    )

    @field_validator("username")
    def validate_username(cls, v):
        for char in v:
            if char in string.whitespace:
                raise ValueError("Username cannot contain whitespace")
        return v.lower()  # Normalize to lowercase


user = User(name="Salman", username="salkhan", age=34, email="salman@outlook.com")

print(User.model_json_schema())
