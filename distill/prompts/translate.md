Translate a JSON study pack from English into the specified target language. Preserve all structure, numeric fields, IDs, and array lengths exactly.

<rules>
1. Translate `text` fields in summaries and `question`/`answer` fields in flashcards into the target language.
2. Translate only the values in `outline_titles` — preserve every key exactly as it appears in the input.
3. Preserve the JSON structure exactly — same keys, same array lengths, same nesting.
4. Preserve all numeric fields: `start_ts`, `end_ts`, `depth`, `section_id`, `section_anchors`.
5. The `quote` field in citations may be translated for readability, but the translation should match the spoken words as closely as possible.
6. Preserve proper nouns, technical terms, and cited names as they appear in the source unless a widely-accepted translated form exists.
7. Do not add or remove flashcards or summaries.
8. Return only valid JSON — no preamble, no markdown fences, no commentary.
</rules>

<output_contract>
Return the translated study pack with the same structure as the input:

```
{
  "summaries": [...],
  "flashcards": [...],
  "outline_titles": {"node-id": "Translated title", ...}
}
```
</output_contract>

Here is an example input with an ideal response.

<example>
<input>
Target language: es

{
  "summaries": [{"depth": "ninety_seconds", "text": "This lecture covers Big-O notation.", "section_anchors": ["ch1"]}],
  "flashcards": [
    {
      "question": "What is Big-O notation?",
      "answer": "Big-O notation describes the upper bound on an algorithm's time complexity as input size grows.",
      "section_id": "ch1-s1",
      "citations": [{"start_ts": 18.0, "end_ts": 30.0, "quote": "f(n) is O(g(n)) if there exist constants c and n₀"}]
    }
  ],
  "outline_titles": {"ch1": "Introduction to Big-O", "ch1-s1": "Definition and Motivation"}
}
</input>
<output>
{
  "summaries": [{"depth": "ninety_seconds", "text": "Esta clase cubre la notación Big-O.", "section_anchors": ["ch1"]}],
  "flashcards": [
    {
      "question": "¿Qué es la notación Big-O?",
      "answer": "La notación Big-O describe el límite superior de la complejidad temporal de un algoritmo a medida que crece el tamaño de la entrada.",
      "section_id": "ch1-s1",
      "citations": [{"start_ts": 18.0, "end_ts": 30.0, "quote": "f(n) es O(g(n)) si existen constantes c y n₀"}]
    }
  ],
  "outline_titles": {"ch1": "Introducción a Big-O", "ch1-s1": "Definición y Motivación"}
}
</output>
<reasoning>Text, question, and answer fields are translated. depth, section_id, section_anchors, start_ts, and end_ts are unchanged. The quote is translated for readability but preserves the mathematical content exactly. outline_titles values are translated; keys ch1 and ch1-s1 are preserved exactly.</reasoning>
</example>
