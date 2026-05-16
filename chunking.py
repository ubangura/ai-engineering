import re


def chunk_by_char(
    text: str, chunk_size: int = 150, chunk_overlap: int = 20
) -> list[str]:
    chunks: list[str] = []
    start_index = 0

    while start_index < len(text):
        end_index = min(start_index + chunk_size, len(text))

        chunk = text[start_index:end_index]
        chunks.append(chunk)

        start_index = end_index - chunk_overlap if end_index < len(text) else len(text)

    return chunks


def chunk_by_sentence(
    text: str, max_sentences_per_chunk: int = 5, overlap_sentences: int = 1
) -> list[str]:
    sentences = re.split(r"(?<=[.!?])\s+", text)

    chunks: list[str] = []
    start_index = 0

    while start_index < len(sentences):
        end_index = min(start_index + max_sentences_per_chunk, len(sentences))

        chunk = sentences[start_index:end_index]
        chunks.append(" ".join(chunk))

        start_index += max_sentences_per_chunk - overlap_sentences

        if start_index < 0:
            start_index = 0

    return chunks


def chunk_by_section(text: str) -> list[str]:
    return re.split(r"\n(?=## )", text)
