from typing import Literal

import voyageai
from dotenv import load_dotenv

load_dotenv()
client = voyageai.Client()


def generate_embedding(
    text: list[str],
    model: str = "voyage-4-lite",
    input_type: Literal["query", "document"] | None = "query",
) -> list[float] | list[int]:
    result = client.embed(texts=text, model=model, input_type=input_type)
    return result.embeddings[0]
