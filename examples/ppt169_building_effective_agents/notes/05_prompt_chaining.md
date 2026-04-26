[Transition] Now let's look at the first workflow pattern: Prompt Chaining.

The diagram shows the core idea — decompose a task into sequential steps. Each LLM call processes the output of the previous one, with optional "gate" checks at intermediate points to ensure quality.

The key trade-off is latency for accuracy. By making each individual LLM call a simpler, more focused task, you get better overall results.

Two concrete examples: generating marketing copy then translating it, or writing a document outline, checking it meets criteria, then writing the full document.

Key points: ① Sequential LLM calls with gate checks ② Trade latency for accuracy ③ Works when tasks decompose into fixed subtasks
Duration: 1.5 minutes