# AI Engineering

Hands-on experiments from AI engineering self-study.

## Structure

| Folder            | Domain                                                          |
| ----------------- | --------------------------------------------------------------- |
| `python-for-ai/`  | Python fundamentals for AI (pandas, matplotlib, APIs, Pydantic) |
| `01-llm-apis/`    | Messages API, structured outputs, prompt engineering, streaming |
| `02-embeddings/`  | Voyage AI, sentence-transformers, semantic search               |
| `03-rag/`         | Chunking, vector DBs, hybrid search, advanced patterns, eval    |
| `04-agents/`      | Tool calling, PydanticAI, LangGraph, MCP, reliability           |
| `05-fine-tuning/` | LoRA/QLoRA, dataset creation, evaluation                        |
| `06-ai-safety/`   | Prompt injection, guardrails, monitoring                        |
| `capstone/`       | Portfolio project integrating all domains                       |

## Provider Stack

| Layer       | Tool                                         |
| ----------- | -------------------------------------------- |
| LLM         | Claude (Anthropic Messages API)              |
| Embeddings  | Voyage AI / sentence-transformers            |
| Vector DB   | Chroma (prototyping) → pgvector (production) |
| Agents      | PydanticAI + LangGraph                       |
| Fine-tuning | Hugging Face + LoRA on Llama/Phi/Mistral     |

## Key Resources

- [Anthropic Messages API](https://docs.anthropic.com/en/api/messages)
- [Anthropic Cookbook](https://github.com/anthropics/anthropic-cookbook)
- [Dave Ebbelaar's ai-cookbook](https://github.com/daveebbelaar/ai-cookbook)
- [LangChain RAG From Scratch](https://github.com/langchain-ai/rag-from-scratch)
- [OWASP Top 10 for LLMs](https://genai.owasp.org/)
