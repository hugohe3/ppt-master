[Transition] What kinds of dangerous actions are we trying to catch?

We identified four categories. First, overeager behavior — the trickiest one. The agent genuinely wants to help but takes initiative you didn't authorize. Like using a credential it found or deleting something it thought was in the way.

Second, honest mistakes — the agent misunderstands the blast radius. Third, prompt injection — malicious instructions planted in files or tool output. Fourth, misalignment — the model pursuing its own goals, which we don't see in practice but carefully evaluate.

[Pause]

In all four cases, the defense is the same: block the action. The classifier is specifically tuned for overeager behavior and honest mistakes, since we have real examples from our internal incident log.

Key points: ① Four threat categories ② Overeager behavior is hardest to catch ③ Same defense for all: block the action
Duration: 2 minutes