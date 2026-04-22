[Transition] Now let's look under the hood. How does this actually work?

Auto Mode uses two layers of defense. At the input layer, a prompt-injection probe scans everything the agent reads — file contents, web fetches, shell output — before it enters the context. If something looks like an injection attempt, the probe adds a warning.

At the output layer, a transcript classifier running on Sonnet 4.6 evaluates each action before it executes. It's a two-stage process: a fast single-token filter that catches most things, followed by chain-of-thought reasoning only when needed. This means we spend reasoning tokens only where they matter.

And the entire pipeline runs recursively for subagents.

Key points: ① Input layer: prompt-injection probe ② Output layer: transcript classifier on Sonnet 4.6 ③ Two-stage filter for efficiency
Duration: 2 minutes