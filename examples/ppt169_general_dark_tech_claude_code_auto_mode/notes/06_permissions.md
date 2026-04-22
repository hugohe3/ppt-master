[Transition] Not every action needs the classifier. Let me walk you through the three-tier system.

Tier 1 is a built-in allowlist — file reads, search, code navigation. These can't modify state, so they pass through immediately. Users can also configure their own always-allow rules, though Auto Mode drops broad interpreter escapes like blanket Python or Node access.

Tier 2 covers in-project file operations. If you're editing source files in your repo, there's no classifier call — version control has your back.

Only the actions with real downside potential reach Tier 3: the transcript classifier. Shell commands, web fetches, external tools, anything outside the project directory. That's where the two-stage filter does its work.

Key points: ① Tier 1: safe-tool allowlist ② Tier 2: in-project edits bypass classifier ③ Tier 3: classifier for real-risk actions
Duration: 1.5 minutes