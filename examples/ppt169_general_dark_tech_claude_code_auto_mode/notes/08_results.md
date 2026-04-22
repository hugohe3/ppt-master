[Transition] Now, the results. We believe in being honest about what works and what doesn't.

We evaluated on three datasets: 10,000 real tool calls, 52 curated overeager actions, and 1,000 synthetic exfiltration attempts. The full pipeline achieves 0.4% false positive rate on real traffic — meaning very little friction for normal use.

The honest number is the 17% false-negative rate on real overeager actions. The classifier usually identifies the danger correctly — it sees the force-push, the deletion. What it gets wrong is whether the user's consent actually covers this specific action.

[Pause]

Is 17% acceptable? If you're comparing against --dangerously-skip-permissions, it's a massive improvement. If you're manually reviewing every action on production infrastructure, Auto Mode isn't meant to replace that judgment.

Key points: ① 0.4% FPR on real traffic ② 17% FNR on overeager actions — the honest number ③ Substantial improvement over no guardrails
Duration: 2 minutes