import re


def chunk_by_section(text: str) -> list[str]:
    return re.split(r"\n## ", text)


with open("../report.md") as f:
    text = f.read()

chunks = chunk_by_section(text)

for chunk in chunks:
    print(f"{chunk} \n---\n")
