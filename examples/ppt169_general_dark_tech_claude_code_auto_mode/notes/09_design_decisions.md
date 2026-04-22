[Transition] Let me highlight three design decisions that shaped this system.

First, the two-stage classification. Stage 1 is a fast filter tuned to be cautious — it accepts an 8.5% false positive rate. Stage 2 adds reasoning and drops that to 0.4%. Because both stages share the same prompt, Stage 2 is almost entirely a cache hit.

Second, compound injection defense. For an injection to succeed, it must evade the input-layer probe AND then produce a tool call that the transcript classifier — which never saw the injection payload — independently judges as safe. Getting past both is significantly harder than either alone.

Third, deny-and-continue. When the classifier blocks an action, the agent doesn't stop. It retries with a safer approach. Three consecutive denials or 20 total trigger escalation to a human.

Key points: ① Two-stage pipeline for efficiency ② Compound defense against injection ③ Deny-and-continue for resilience
Duration: 2 minutes