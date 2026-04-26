# 01_cover

Welcome everyone to this session on Building Effective Agents. This presentation distills key insights from Anthropic's engineering team, drawing from their experience working with dozens of teams building LLM agents across industries.

The central thesis is compelling: the most successful implementations aren't using complex frameworks. They're building with simple, composable patterns.

[Pause]

Let's explore what those patterns look like and when to use them.

Key points: ① Anthropic's field-tested agent patterns ② Simplicity beats complexity ③ Practical implementation guidance
Duration: 1.5 minutes

---

# 02_what_are_agents

[Transition] Before diving into patterns, we need to establish a shared vocabulary.

Anthropic draws an important architectural distinction between two types of agentic systems. On the left, we have Workflows — systems where LLMs and tools follow predefined code paths. Think of these as choreographed sequences. On the right, Agents — systems where the LLM itself decides what to do next, dynamically directing its own processes.

[Pause]

The key takeaway here is that both are "agentic systems." It's a spectrum, not a binary — and the right choice depends on your specific use case.

Key points: ① Workflows = predefined orchestration ② Agents = autonomous tool-using LLMs ③ Both are valid — spectrum matters more than label
Duration: 1.5 minutes

---

# 03_when_to_use_agents

[Transition] So when should you reach for these more complex patterns?

The answer starts on the left: most of the time, you should start with single LLM calls optimized with retrieval and in-context examples. This covers the vast majority of applications.

When you do need more, workflows give you predictability for well-defined tasks, while agents shine when flexibility and model-driven decisions are needed at scale.

[Interactive] Think about your current project — where does it fall on this complexity spectrum?

And a crucial piece of advice about frameworks: start with raw LLM APIs. Many patterns need just a few lines of code. If you do use a framework, make sure you understand what's happening underneath.

Key points: ① Start simple — single LLM calls first ② Workflows for defined tasks, agents for flexibility ③ Understand your frameworks
Duration: 2 minutes

---

# 04_augmented_llm

[Transition] Every agentic system starts from the same building block: the augmented LLM.

This diagram shows the foundational unit. You take a base LLM and enhance it with three capabilities: retrieval for accessing relevant information, tools for taking actions in the world, and memory for retaining context across interactions.

[Pause]

Two things matter most in implementation: tailor these capabilities to your specific use case, and ensure they provide well-documented interfaces. Anthropic's Model Context Protocol — MCP — is one approach to standardizing third-party tool integration.

Key points: ① LLM + retrieval + tools + memory ② Tailor capabilities to use case ③ MCP for standardized integration
Duration: 1.5 minutes

---

# 05_prompt_chaining

[Transition] Now let's look at the first workflow pattern: Prompt Chaining.

The diagram shows the core idea — decompose a task into sequential steps. Each LLM call processes the output of the previous one, with optional "gate" checks at intermediate points to ensure quality.

The key trade-off is latency for accuracy. By making each individual LLM call a simpler, more focused task, you get better overall results.

Two concrete examples: generating marketing copy then translating it, or writing a document outline, checking it meets criteria, then writing the full document.

Key points: ① Sequential LLM calls with gate checks ② Trade latency for accuracy ③ Works when tasks decompose into fixed subtasks
Duration: 1.5 minutes

---

# 06_routing

[Transition] The second pattern is Routing — classifying inputs to direct them to specialized handlers.

Routing lets you build more specialized prompts without cross-contamination. Optimizing for one type of input won't hurt performance on others.

Think of customer service: general questions, refund requests, and technical support each flow to different downstream processes with tailored prompts and tools. Or model selection — easy questions go to smaller, cost-efficient models like Haiku, while complex ones route to more capable models like Sonnet.

Key points: ① Classify input → specialized followup ② Separation of concerns ③ Prevents cross-optimization interference
Duration: 1.5 minutes

---

# 07_parallelization

[Transition] The third pattern is Parallelization, which comes in two flavors.

Sectioning breaks a task into independent subtasks that run simultaneously — like having one model process queries while another screens for inappropriate content. These tend to perform better than asking a single LLM call to do both.

Voting runs the same task multiple times for diverse perspectives — like having several different prompts review code for vulnerabilities, flagging issues independently.

[Pause]

Both approaches boost confidence through multiple perspectives.

Key points: ① Sectioning = independent parallel subtasks ② Voting = multiple perspectives on same task ③ Better than single-call for complex multi-concern tasks
Duration: 2 minutes

---

# 08_orchestrator_workers

[Transition] The Orchestrator-Workers pattern looks similar to parallelization, but has one crucial difference.

Here, a central LLM dynamically decides what subtasks are needed, delegates them to worker LLMs, and synthesizes the results. The subtasks aren't predetermined — they emerge from the input.

This is ideal for coding products that modify multiple files, where the orchestrator determines which files need changes based on the task description. Or search tasks that need to gather and analyze information from multiple sources.

Key points: ① Central LLM dynamically breaks down tasks ② Key difference: subtasks not pre-defined ③ Ideal for unpredictable, complex workflows
Duration: 1.5 minutes

---

# 09_evaluator_optimizer

[Transition] The last workflow pattern is the Evaluator-Optimizer — essentially an iterative refinement loop.

One LLM generates a response; another evaluates it and provides feedback. This cycle continues until the output meets quality standards. It's analogous to how a human writer iterates through drafts.

There are two clear signs this pattern fits: first, human feedback demonstrably improves LLM responses; second, the LLM can provide that same kind of feedback. If both are true, you have a strong candidate.

Key points: ① Generate-evaluate feedback loop ② Two fitness signals to look for ③ Analogous to human iterative writing
Duration: 1.5 minutes

---

# 10_agents

[Transition] Now we arrive at fully autonomous agents — the most flexible and powerful pattern.

Agents emerge as LLMs mature across five key capabilities: understanding complex inputs, reasoning and planning, reliable tool use, error recovery, and knowing when to pause for human checkpoints.

[Pause]

Here's the surprising part — agent implementation is often straightforward. They're typically just LLMs using tools in a feedback loop. But this simplicity comes with trade-offs: higher costs and potential for compounding errors. Extensive testing in sandboxed environments, with appropriate guardrails, is essential.

Key points: ① Five key LLM capabilities enable agents ② Implementation = LLMs using tools in a loop ③ Higher costs + compounding errors require guardrails
Duration: 2 minutes

---

# 11_agents_in_practice

[Transition] Let's look at two domains where agents have proven particularly valuable.

Customer support is a natural fit — conversations require both dialogue and action. Tools pull customer data, handle refunds, and access knowledge bases. Some companies are so confident in their agents that they charge only for successful resolutions.

Coding agents have shown remarkable potential. The key advantage: code is verifiable through automated tests, creating a natural feedback loop. Anthropic's own agent solves real GitHub issues from pull request descriptions alone.

One fascinating insight from their experience: they spent more time optimizing their tools than the overall prompt — a testament to how important ACI design is.

Key points: ① Customer support: natural conversation + actions ② Coding agents: verifiable + iterable ③ Tool optimization > prompt optimization
Duration: 2 minutes

---

# 12_summary

[Transition] Let's close with three principles to take away.

First, simplicity. Build the right system for your needs, not the most sophisticated one you can imagine.

Second, transparency. Let your users see the agent's reasoning — it builds trust and aids debugging.

Third, invest in ACI design — your agent-computer interface. Think of it as HCI for machines. Good tool documentation and testing pays dividends.

[Pause]

The progression is clear: start simple, optimize with evaluation, and add agentic systems only when simpler solutions genuinely fall short. Thank you.

Key points: ① Simplicity in design ② Transparency in planning ③ ACI through tool documentation and testing
Duration: 2 minutes
