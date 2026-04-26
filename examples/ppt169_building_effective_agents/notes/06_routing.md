[Transition] The second pattern is Routing — classifying inputs to direct them to specialized handlers.

Routing lets you build more specialized prompts without cross-contamination. Optimizing for one type of input won't hurt performance on others.

Think of customer service: general questions, refund requests, and technical support each flow to different downstream processes with tailored prompts and tools. Or model selection — easy questions go to smaller, cost-efficient models like Haiku, while complex ones route to more capable models like Sonnet.

Key points: ① Classify input → specialized followup ② Separation of concerns ③ Prevents cross-optimization interference
Duration: 1.5 minutes