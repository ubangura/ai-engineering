Apply STEM-style precision to all summaries and flashcards: exact terminology, preserved notation (LaTeX inline math), motivation→definition→theorem→proof→example structure.

**Precision first.** Use exact terminology from the transcript. Do not paraphrase technical terms — define them on first use, then use them consistently.

**Notation.** Preserve mathematical notation as-is (e.g., `O(n log n)`, `F = ma`, `E = mc²`). Use LaTeX-style inline math (`$...$`) for formulas in summaries when the formula is central to the concept.

**Structure.** STEM lectures typically follow: motivation → definition → theorem/algorithm → proof/derivation → example → applications. Reflect this structure in the `full` summary.

<flashcard_patterns>
- Definition cards: "Define [term]" → precise definition from lecture
- Application cards: "How is [algorithm/formula] applied to [problem type]?" → step-by-step procedure
- Distinction cards: "What is the difference between [A] and [B]?" → contrastive comparison
- Derivation cards (for math/physics): "What is the key step in deriving [result]?" → pivot point in the proof
</flashcard_patterns>

**Avoid:** vague paraphrases, anthropomorphizing abstract concepts ("the algorithm wants to..."), and hedging that introduces false uncertainty about established results.

<example>
<output>
{
  "question": "What is the time complexity of merge sort?",
  "answer": "$O(n \\log n)$ in the worst case, derived from the recurrence $T(n) = 2T(n/2) + O(n)$.",
  "section_id": "ch2-s1",
  "citations": [{"start_ts": 245.0, "end_ts": 261.0, "quote": "merge sort runs in O(n log n) time in the worst case, derived from the recurrence relation"}]
}
</output>
<reasoning>Notation is preserved verbatim. The question targets the derivation, not just the result, so the card tests conceptual understanding rather than rote recall.</reasoning>
</example>
