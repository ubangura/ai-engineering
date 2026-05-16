from vector_databases.vector_index import VectorIndex

from chunking import chunk_by_section
from embedding import generate_embedding

# 1. Chunk document
with open("./report.md", "r") as f:
    text = f.read()

chunks = chunk_by_section(text)

# 2. Generate embeddings
embeddings = generate_embedding(texts=chunks, input_type="document")

vector_store = VectorIndex()

# 3. Populate vector store
for chunk, embedding in zip(chunks, embeddings):
    vector_store.add_vector(embedding, {"content": chunk})

# 4. Generate query embedding
[query_embedding] = generate_embedding(
    texts=["What did the software engineering dept do last year?"],
    input_type="query",
)

# 5. Search
results = vector_store.search(query=query_embedding, top_k=2)

for doc, distance in results:
    print(distance, "\n", doc["content"][0:200], "\n")
