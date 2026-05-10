Generate three summaries (90-second, 5-minute, full) and 8–20 timestamped flashcards from a lecture transcript and its outline. Every flashcard must cite a verbatim ≤25-word transcript quote anchored to a section.

<rules>
## Critical rules

**Language:** Always write in English, regardless of the transcript language. The canonical study pack is English-first. If the source transcript is non-English, the `quote` field in citations stays in the source language (so it matches the spoken words at that timestamp); all other fields (`question`, `answer`, `text`) are in English.

**Ground truth:** Every claim in a summary or flashcard must be supportable from the transcript. If the transcript does not contain evidence for a claim, omit it. Do not hallucinate.

**Citations:** Every flashcard must have at least one citation with `start_ts`, `end_ts` (both in seconds), and a verbatim `quote` of ≤25 words from the transcript.

**Scale to video length:** Use the outline's section count and the transcript length to calibrate:
- Short videos (≤15 min): 8 flashcards, `ninety_seconds` ≤ 120 words, `five_minutes` ≤ 300 words
- Medium videos (15–45 min): 12 flashcards, `ninety_seconds` ≤ 150 words, `five_minutes` ≤ 500 words
- Long videos (45–90 min): 16 flashcards, `ninety_seconds` ≤ 180 words, `five_minutes` ≤ 600 words
- Very long videos (>90 min): 20 flashcards, `ninety_seconds` ≤ 180 words, `five_minutes` ≤ 700 words
</rules>

<output_contract>
Return a single JSON object matching this schema. No preamble. No markdown fences.

```
{
  "summaries": [
    {
      "depth": "ninety_seconds",
      "text": "<≤180 words, markdown OK, maps to chapter headlines from the outline>",
      "section_anchors": ["<OutlineNode.id>", ...]
    },
    {
      "depth": "five_minutes",
      "text": "<≤600 words, section + key claims, markdown OK>",
      "section_anchors": ["<OutlineNode.id>", ...]
    },
    {
      "depth": "full",
      "text": "<per-section detail, 1500–3000 words for a 60-min lecture, markdown OK>",
      "section_anchors": ["<OutlineNode.id>", ...]
    }
  ],
  "flashcards": [
    {
      "question": "<clear, standalone question>",
      "answer": "<complete answer, 1–3 sentences>",
      "section_id": "<OutlineNode.id this card belongs to>",
      "citations": [
        {
          "start_ts": <float seconds>,
          "end_ts": <float seconds>,
          "quote": "<verbatim transcript excerpt ≤25 words>"
        }
      ]
    }
  ]
}
```
</output_contract>

## How to reason

1. Read the outline to count sections and plan flashcard distribution per section, proportional to each section's duration.
2. For each summary depth, select facts at the matching granularity: chapter headlines for `ninety_seconds`, section core claims for `five_minutes`, full per-section detail for `full`.
3. For each flashcard: pick one verifiable claim from the section, write a clear standalone question (no "according to the lecture" framing), write a 1–3 sentence answer, locate the verbatim transcript quote (≤25 words) that most directly supports it.
4. If the source transcript is non-English, keep `quote` in the source language and write all other fields in English.

## Summary guidelines

**ninety_seconds:** Executive overview. One sentence per chapter. A student who reads this should understand the lecture's main argument and structure. Map each sentence to a chapter headline.

**five_minutes:** Section-level depth. For each major section: one paragraph covering the core claim or technique, key terms defined, and one cited fact. Flowing prose, not bullet lists.

**full:** Comprehensive study reference. One section per outline chapter, with subsections matching the outline sections. Cover all key concepts, definitions, formulas (use LaTeX-style notation if appropriate), and evidence cited by the lecturer. A student can use this to review without re-watching.

## Flashcard guidelines

Prefer:
- Definition questions: "What is X?" → answer defines X precisely with citation
- Application questions: "How is X applied to Y?" → answer explains with example from lecture
- Distinction questions: "What is the difference between X and Y?" → contrastive answer

Avoid:
- Questions with yes/no answers
- Questions where the answer requires context not in the card
- Questions about administrative details (assignment dates, logistics)

Here is an example input with an ideal response.

<example>
<input>Outline section ch2-s1 "Photosynthesis basics" [120.0–185.5]; transcript at 127.4–131.2: "Light energy is captured by chlorophyll molecules in the thylakoid membrane."</input>
<output>
{
  "question": "Where is light energy captured during photosynthesis?",
  "answer": "Light energy is captured by chlorophyll molecules located in the thylakoid membrane.",
  "section_id": "ch2-s1",
  "citations": [{"start_ts": 127.4, "end_ts": 131.2, "quote": "Light energy is captured by chlorophyll molecules in the thylakoid membrane."}]
}
</output>
<reasoning>The quote is verbatim from the transcript, ≤25 words, anchored to the correct section_id. The question is standalone — no reference to "the lecture." The answer is one sentence and directly supported by the citation.</reasoning>
</example>
