[Transition] Here's one of the most interesting design decisions: what the classifier actually sees.

We strip the assistant's own text — so the agent can't talk the classifier into a bad call with persuasive rationalizations. We also strip tool results, which is the primary defense against prompt injection.

What's left? Just user messages and the bare tool call commands. The classifier judges what the agent did, not what the agent said.

[Pause]

There's a useful side effect: being reasoning-blind makes this complementary to chain-of-thought monitoring. One catches bad actions, the other catches bad reasoning. Together they're stronger than either alone.

Key points: ① Strip assistant text and tool results ② Judge actions, not words ③ Complementary to CoT monitoring
Duration: 1.5 minutes