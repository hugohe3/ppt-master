# 01_cover

Welcome everyone. Today I'm going to walk you through one of our recent engineering efforts at Anthropic — Claude Code's Auto Mode.

[Pause]

This is a deep dive into how we built a classifier-based permission system that makes autonomous coding substantially safer, without the friction of clicking "approve" hundreds of times.

Key points: ① Introducing Claude Code Auto Mode ② Balancing safety and autonomy ③ Engineering blog walkthrough
Duration: 1 minute

---

# 02_approval_fatigue

[Transition] Before we get into the solution, let's understand the problem we're solving.

Here's the number that drove this project: 93% of permission prompts in Claude Code are approved. That means users are clicking "approve" on nearly everything — and over time, they stop paying attention. That's approval fatigue, and it's a real security risk.

Before Auto Mode, users had two choices. A sandbox that's safe but breaks whenever you need network access. Or the dangerously-skip-permissions flag — zero friction, but zero protection. We've seen the consequences: agents deleting remote branches, uploading auth tokens, even trying migrations against production databases.

[Pause]

Neither option was good enough. We needed something in between.

Key points: ① 93% approval rate creates fatigue ② Existing options are sandbox or no guardrails ③ Real incidents demonstrate the risk
Duration: 2 minutes

---

# 03_auto_mode

[Transition] That's where Auto Mode comes in.

Auto Mode delegates permission decisions to model-based classifiers. Think of it as a middle ground — it's not asking you to approve every file edit, but it's also not letting the agent do whatever it wants.

The goal is simple: catch the dangerous actions that aren't aligned with what you actually asked for, and let everything else run without interruption. Three pillars: catch danger, stay fast, keep autonomy.

You can start using it today — just run claude auto-mode defaults.

Key points: ① Classifier-delegated approvals ② Middle ground between manual and no guardrails ③ Immediately available
Duration: 1.5 minutes

---

# 04_architecture

[Transition] Now let's look under the hood. How does this actually work?

Auto Mode uses two layers of defense. At the input layer, a prompt-injection probe scans everything the agent reads — file contents, web fetches, shell output — before it enters the context. If something looks like an injection attempt, the probe adds a warning.

At the output layer, a transcript classifier running on Sonnet 4.6 evaluates each action before it executes. It's a two-stage process: a fast single-token filter that catches most things, followed by chain-of-thought reasoning only when needed. This means we spend reasoning tokens only where they matter.

And the entire pipeline runs recursively for subagents.

Key points: ① Input layer: prompt-injection probe ② Output layer: transcript classifier on Sonnet 4.6 ③ Two-stage filter for efficiency
Duration: 2 minutes

---

# 05_threat_model

[Transition] What kinds of dangerous actions are we trying to catch?

We identified four categories. First, overeager behavior — the trickiest one. The agent genuinely wants to help but takes initiative you didn't authorize. Like using a credential it found or deleting something it thought was in the way.

Second, honest mistakes — the agent misunderstands the blast radius. Third, prompt injection — malicious instructions planted in files or tool output. Fourth, misalignment — the model pursuing its own goals, which we don't see in practice but carefully evaluate.

[Pause]

In all four cases, the defense is the same: block the action. The classifier is specifically tuned for overeager behavior and honest mistakes, since we have real examples from our internal incident log.

Key points: ① Four threat categories ② Overeager behavior is hardest to catch ③ Same defense for all: block the action
Duration: 2 minutes

---

# 06_permissions

[Transition] Not every action needs the classifier. Let me walk you through the three-tier system.

Tier 1 is a built-in allowlist — file reads, search, code navigation. These can't modify state, so they pass through immediately. Users can also configure their own always-allow rules, though Auto Mode drops broad interpreter escapes like blanket Python or Node access.

Tier 2 covers in-project file operations. If you're editing source files in your repo, there's no classifier call — version control has your back.

Only the actions with real downside potential reach Tier 3: the transcript classifier. Shell commands, web fetches, external tools, anything outside the project directory. That's where the two-stage filter does its work.

Key points: ① Tier 1: safe-tool allowlist ② Tier 2: in-project edits bypass classifier ③ Tier 3: classifier for real-risk actions
Duration: 1.5 minutes

---

# 07_classifier

[Transition] Here's one of the most interesting design decisions: what the classifier actually sees.

We strip the assistant's own text — so the agent can't talk the classifier into a bad call with persuasive rationalizations. We also strip tool results, which is the primary defense against prompt injection.

What's left? Just user messages and the bare tool call commands. The classifier judges what the agent did, not what the agent said.

[Pause]

There's a useful side effect: being reasoning-blind makes this complementary to chain-of-thought monitoring. One catches bad actions, the other catches bad reasoning. Together they're stronger than either alone.

Key points: ① Strip assistant text and tool results ② Judge actions, not words ③ Complementary to CoT monitoring
Duration: 1.5 minutes

---

# 08_results

[Transition] Now, the results. We believe in being honest about what works and what doesn't.

We evaluated on three datasets: 10,000 real tool calls, 52 curated overeager actions, and 1,000 synthetic exfiltration attempts. The full pipeline achieves 0.4% false positive rate on real traffic — meaning very little friction for normal use.

The honest number is the 17% false-negative rate on real overeager actions. The classifier usually identifies the danger correctly — it sees the force-push, the deletion. What it gets wrong is whether the user's consent actually covers this specific action.

[Pause]

Is 17% acceptable? If you're comparing against --dangerously-skip-permissions, it's a massive improvement. If you're manually reviewing every action on production infrastructure, Auto Mode isn't meant to replace that judgment.

Key points: ① 0.4% FPR on real traffic ② 17% FNR on overeager actions — the honest number ③ Substantial improvement over no guardrails
Duration: 2 minutes

---

# 09_design_decisions

[Transition] Let me highlight three design decisions that shaped this system.

First, the two-stage classification. Stage 1 is a fast filter tuned to be cautious — it accepts an 8.5% false positive rate. Stage 2 adds reasoning and drops that to 0.4%. Because both stages share the same prompt, Stage 2 is almost entirely a cache hit.

Second, compound injection defense. For an injection to succeed, it must evade the input-layer probe AND then produce a tool call that the transcript classifier — which never saw the injection payload — independently judges as safe. Getting past both is significantly harder than either alone.

Third, deny-and-continue. When the classifier blocks an action, the agent doesn't stop. It retries with a safer approach. Three consecutive denials or 20 total trigger escalation to a human.

Key points: ① Two-stage pipeline for efficiency ② Compound defense against injection ③ Deny-and-continue for resilience
Duration: 2 minutes

---

# 10_closing

[Transition] So where does this leave us?

Auto Mode catches enough dangerous actions to make autonomous operation substantially safer than running with no guardrails. The classifier doesn't need to be perfect to be valuable.

We'll continue expanding our overeagerness testset, iterating on both safety and cost. We encourage users to stay aware of residual risk, use judgment about which tasks to run autonomously, and — importantly — tell us when Auto Mode gets things wrong.

[Pause]

You can start right now with claude auto-mode defaults. Thank you.

Key points: ① Substantially safer than no guardrails ② Not a replacement for careful review on high-stakes tasks ③ Available now — try it
Duration: 1 minute
