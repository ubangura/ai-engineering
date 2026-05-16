from typing import Literal

import voyageai
from dotenv import load_dotenv

load_dotenv()
client = voyageai.Client()  # pyright: ignore[reportPrivateImportUsage]


def generate_embedding(
    texts: list[str],
    model: str = "voyage-4-lite",
    input_type: Literal["query", "document"] | None = "query",
) -> list[list[float]] | list[list[int]]:
    result = client.embed(texts=texts, model=model, input_type=input_type)
    return result.embeddings
