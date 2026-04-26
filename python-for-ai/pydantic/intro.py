from pydantic import BaseModel


class User(BaseModel):
    id: int
    email: str
    age: int


user = User(id=1, email="me@email.com", age=15)

user = User(id=1, email=None, age="Unknown")
