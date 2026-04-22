[Transition] Before we get into the solution, let's understand the problem we're solving.

Here's the number that drove this project: 93% of permission prompts in Claude Code are approved. That means users are clicking "approve" on nearly everything — and over time, they stop paying attention. That's approval fatigue, and it's a real security risk.

Before Auto Mode, users had two choices. A sandbox that's safe but breaks whenever you need network access. Or the dangerously-skip-permissions flag — zero friction, but zero protection. We've seen the consequences: agents deleting remote branches, uploading auth tokens, even trying migrations against production databases.

[Pause]

Neither option was good enough. We needed something in between.

Key points: ① 93% approval rate creates fatigue ② Existing options are sandbox or no guardrails ③ Real incidents demonstrate the risk
Duration: 2 minutes