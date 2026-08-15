# Language Rule

> Applies to every agent-facing file in the package — `skills/ppt-master/SKILL.md`, `references/*.md`, `workflows/**/*.md` — and to repository documentation under `docs/`.

## 1. One Language Per File

Each Markdown file is single-language. New files mirror the language of their siblings in the same directory. Never mix English scaffolding with Chinese paragraphs (or the reverse) inside one file.

`docs/zh/`, `README_CN.md`, `SPONSORS_CN.md`, and other wholly Chinese files are complete translations, not exceptions to this rule — they are single-language too.

## 2. A Non-English Language May Be Content, Never a Rule

Inside an English file, a non-English string is allowed only when it *is* the subject matter. It is never the wording of an instruction to the model.

| Allowed — the string is content | Forbidden — the string is the rule |
|---|---|
| A trigger phrase the user literally types (`继续生成 projects/<name>`) | A decision rule written in Chinese (`语速：edge 默认 +0%…`) |
| A sample field value in an example JSON / notes block | A selection criterion phrased in Chinese (`财报 → 稳重男声`) |
| A label the deck renders on the page (`情景数据`) | An English sentence with a Chinese word standing in for its own term |
| A pronunciation or typography example (`百分之六十八` for TTS) | A section heading or table header in Chinese |
| A proper noun with English context (`印章`, `新中式`) | A prose paragraph of instructions in Chinese |
| A directory or brand name that is genuinely Chinese | |

**Hard rule**: an instruction the model must follow is written in the file's own language. A rule written in one language biases the model's output toward that language and silently overrides [`SKILL.md`](../../skills/ppt-master/SKILL.md)'s "match the user's language" discipline.

## 3. Never Hard-Code the Output Language

Do not write a rule that fixes which language the model replies in — `write a one-line Chinese description` is a defect. Say "in the user's chat language" instead.

A user-facing message template written in one concrete language is content under §2, so it stays; but it must carry an explicit "translate to the user's chat language if different" note.

## 4. Trigger Text Stays Language-Neutral

`SKILL.md`'s `description` is English prose. Do not append per-language keyword lists to it, and do not name a specific agent host or harness in it. When a request intent triggers unreliably, widen the English intent vocabulary (nouns and verbs users actually type, including language-neutral tokens such as `PPT` / `PPTX`) rather than adding another language's keywords — the language list has no natural end, and every entry costs budget on a file loaded on every run.
