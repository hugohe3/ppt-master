# What Is a PPT?

[English](./what-is-ppt.md) | [Chinese](./zh/what-is-ppt.md)

---

This document explains what people mean by “PPT,” why they create presentations, how a PowerPoint document is structured, and what makes the medium suitable or unsuitable for a communication task.

It treats PPT as a communication medium, an editable document, a delivery format, and a native file structure—not merely as a set of slides.

## 1. “PPT” Names Several Different Things

In ordinary usage, “PPT” is overloaded. A useful discussion separates at least five meanings:

| Meaning | Definition |
|---|---|
| PowerPoint | Microsoft’s authoring, editing, presenting, and collaboration application |
| Presentation | A communication event involving a message, an audience, a delivery context, and an intended outcome |
| Deck | The ordered, editable presentation document used before, during, and after that event |
| Slide show | The performed or played-back sequence, potentially including transitions, animation, narration, video, and timing |
| PPT/PPTX file | The digital package that stores slides, reusable structure, media, notes, comments, relationships, and presentation behavior |

Microsoft describes PowerPoint as a tool for creating presentations from scratch or templates, combining text, images, art, and video, adding transitions and animation, and sharing the result with others. That capability list already shows that a presentation is more than a stack of static pages. See [Microsoft’s PowerPoint overview](https://support.microsoft.com/en-us/powerpoint/training/what-is-powerpoint).

In this document, **PPT means a PowerPoint-class presentation artifact and its communication use**, not only the legacy `.ppt` extension.

### 1.1 Common file types

| Extension | Role |
|---|---|
| `.ppt` | Legacy PowerPoint 97–2003 binary presentation |
| `.pptx` | Current macro-free PowerPoint presentation package and the main editable format used by modern PowerPoint |
| `.pptm` | Macro-enabled PowerPoint presentation |
| `.potx` | Reusable PowerPoint template |
| `.ppsx` | PowerPoint show that opens directly in Slide Show view |

The current formats and their intended uses are documented in [Microsoft’s file-format reference](https://support.microsoft.com/en-us/powerpoint/file-formats-that-are-supported-in-powerpoint). Modern `.pptx` is an Office Open XML package whose vocabularies and packaging are standardized by [ECMA-376 / ISO/IEC 29500](https://ecma-international.org/publications-and-standards/standards/ecma-376/).

---

## 2. Why People Create Presentations

People rarely want “slides” as an end in themselves. They want to change what an audience knows, understands, believes, decides, or does, and often to leave behind an organizational artifact.

```text
Source material + intent
→ ordered argument or explanation
→ shared visual experience
→ audience outcome
+ editable, distributable record
```

| Communication job | Intended change after the presentation |
|---|---|
| Inform | The audience knows facts it did not know before |
| Explain | The audience understands a mechanism, relationship, or cause |
| Persuade | The audience accepts or seriously considers a position |
| Decide | A group moves from alternatives to a choice |
| Align | Participants share priorities, language, and next steps |
| Teach | Learners can understand, remember, or perform something |
| Report and account | Stakeholders can assess progress, evidence, risk, and ownership |
| Mobilize | People move from awareness to action |
| Record and hand off | The organization retains an approvable, auditable, reusable artifact |

A single deck may serve several jobs. The useful question is not which one label wins, but how those jobs relate: whether any outcome leads, which ones support one another, and in what sequence. A “status update,” for example, may report progress, expose risk, and request a decision in the same flow.

Organizational-communication research treats recurring forms such as proposals, meetings, and reports as socially recognized responses to recurring situations and purposes. That framing is useful here: a deck is not a neutral container; it participates in an organizational communication practice. See Yates and Orlikowski, [“Genres of Organizational Communication”](https://doi.org/10.5465/amr.1992.4279545).

---

## 3. Why Use PowerPoint Instead of Another Medium

PowerPoint is valuable when a task needs several properties at once:

| Property | Value |
|---|---|
| Sequence | The author can control or propose an order of attention |
| Modularity | Slides can be reordered, hidden, duplicated, replaced, or reused |
| Multimedia composition | Text, diagrams, data, pictures, audio, and video can coexist within a slide; animation adds change over time, and transitions connect slides |
| Presenter support | Notes, Presenter View, timing, and navigation support live delivery |
| Reader support | Reading View, comments, notes pages, handouts, and sharing support asynchronous review |
| Editability | The artifact can be revised, localized, extended, and repurposed |
| Organizational portability | The same artifact can move through meetings, review, approval, archive, and reuse |

PowerPoint should not be the default for every information task:

| Primary need | Often better primary medium |
|---|---|
| Long, linear, self-contained argument | Document or report |
| Live exploration of changing data | Spreadsheet, notebook, or dashboard |
| Open-ended group discovery | Whiteboard or collaborative canvas |
| Fixed, repeatable playback with no editing requirement | Video |
| Interactive navigation and rich user input | Web application |
| Sequential, visual, editable communication that must also circulate | PowerPoint |

The choice is therefore scenario-dependent. “Can this be expressed as slides?” is weaker than “Is a sequenced, modular, editable presentation artifact the right medium for this job?”

---

## 4. A PPT Has More Than One Life

A deck commonly serves different purposes across its lifecycle:

| Stage | Role of the deck |
|---|---|
| Before the event | A thinking, synthesis, review, and rehearsal tool |
| During the event | A shared visual surface that coordinates attention and pacing |
| After the event | A reading copy, decision record, handout, approval artifact, or reusable source |
| Without a live event | An asynchronously read, recorded, narrated, or self-running presentation |

PowerPoint itself exposes separate editing, Slide Show, Presenter, Reading, Notes, Handout, and Master views. Microsoft explicitly recommends Presenter View for delivery with private notes and Reading View for reviewing a presentation without a presenter. See [Choose the right view for the task](https://support.microsoft.com/en-US/PowerPoint/training/choose-the-right-view-for-the-task-in-powerpoint).

### 4.1 Delivery context changes the design

| Primary context | What the deck must optimize for |
|---|---|
| Presenter-led | Distance legibility, pacing, visual anchors, and complementing speech |
| Reader-led | Self-contained reasoning, explicit context, denser evidence, and navigability |
| Hybrid | A clear primary mode plus notes, appendix, or supporting detail for the secondary mode |
| Recorded or self-running | Narration, timing, transitions, playback reliability, and no dependence on a live presenter |

The same slide cannot be assumed to optimize all four contexts. A sparse, speaker-led slide may fail as a standalone decision record; a dense board memo may fail on a large screen. The primary delivery context must be explicit before page density and typography are chosen.

Microsoft’s support for [speaker notes and handouts](https://support.microsoft.com/en-US/PowerPoint/print-your-handouts-notes-or-slides), [recorded narration and timings](https://support.microsoft.com/en-us/PowerPoint/training/record-a-slide-show-with-narration-and-slide-timings), and [sharing and co-authoring](https://support.microsoft.com/en-us/powerpoint/training/share-your-powerpoint-presentation-with-others) is further evidence that a PowerPoint artifact spans performance, reading, distribution, and reuse.

---

## 5. The Native PowerPoint Object Model

A `.pptx` file is a package of related parts, not one bitmap per slide and not one monolithic XML document. Microsoft’s [PresentationML structure guide](https://learn.microsoft.com/en-us/office/open-xml/presentation/structure-of-a-presentationml-document) identifies Presentation, Theme, Slide Master, Slide Layout, and Slide as core parts, with optional notes, handouts, comments, media, transitions, and animation.

```text
Presentation package
├── Theme
├── Slide Master A
│   ├── Slide Layout A1
│   │   ├── Slide 1
│   │   └── Slide 4
│   └── Slide Layout A2
│       └── Slide 2
├── Slide Master B
│   └── Slide Layout B1
│       └── Slide 7
├── Notes / Handouts / Comments
└── Media / Charts / Tables / Transitions / Animation / Audio
```

| Object | Responsibility |
|---|---|
| Theme | Reusable colors, fonts, and effects |
| Slide Master | Shared formatting and objects for a family of layouts |
| Slide Layout | Default appearance, positioning, and placeholders for a slide type |
| Placeholder | A preformatted, typed content container on a layout |
| Slide | One content instance associated with a layout |
| Notes and handouts | Presenter and audience channels beyond the visible slide |
| Package relationships | Connections among slides, layouts, masters, media, notes, comments, and other parts |
| Presentation behavior | Ordering, transitions, animation, narration, and timing |

Microsoft defines slide layouts as containers for formatting, positioning, and placeholders, and shows them as children of a slide master. See [What is a slide layout?](https://support.microsoft.com/en-US/PowerPoint/what-is-a-slide-layout).

This hierarchy matters because a visually correct screenshot can still be a structurally poor PowerPoint. A real deck also needs useful object boundaries, inheritance, editability, relationships, and delivery behavior.

---

## 6. What a PowerPoint Template Is

Microsoft distinguishes a theme from a template: a theme supplies coordinated colors, fonts, and effects, while a template adds content and structure for a particular purpose. See [Themes versus templates](https://support.microsoft.com/en-us/powerpoint/understand-the-difference-between-powerpoint-templates-and-themes).

That definition leads to a practical principle:

> A template exists because a presentation identity, structure, or communication scenario is expected to recur.

In practice, a PowerPoint template can combine several reusable layers:

| Layer | What it contributes |
|---|---|
| Theme | Coordinated colors, fonts, and effects |
| Slide Master | Shared formatting and fixed objects for a family of layouts |
| Slide Layout | Placeholder structure and default composition for a recurring slide type |
| Boilerplate and sample content | Starting slides, recurring wording, examples, and guidance for a particular purpose |

Templates reduce repeated setup, preserve visual and structural consistency, encode recurring presentation patterns, and make later editing and review more predictable. A deck may be copied or used as a reference, but visual similarity alone does not make it a well-structured template. A useful template separates stable, reusable decisions from content that belongs only to one presentation.

---

## 7. What Makes a PPT Good

A good deck is not defined by visual polish alone. Quality is layered:

| Layer | Core question |
|---|---|
| Factual | Are claims, values, sources, and distinctions correct? |
| Communicative | Is the audience, desired outcome, central message, and call to action clear? |
| Narrative | Does the sequence create the intended understanding, judgment, or decision? |
| Cognitive | Can people perceive, process, and connect the information without avoidable overload? |
| Visual | Do hierarchy, typography, space, imagery, and data graphics support meaning? |
| Native and operational | Can the deck be presented, edited, reviewed, reused, and delivered reliably? |

Research does not support “add more visuals” as a universal rule. Mayer’s synthesis of multimedia-learning research emphasizes that well-designed combinations of words and graphics can improve understanding, while human processing capacity is limited. See [Multimedia Learning](https://www.cambridge.org/highereducation/books/multimedia-learning/FB7E79A165D24D47CEACEB4D2C426ECD).

Bartsch and Cobern found that irrelevant pictures and sounds could harm recall and learning even when PowerPoint itself was useful. See [“Effectiveness of PowerPoint presentations in lectures”](https://doi.org/10.1016/S0360-1315(03)00027-7). Kosslyn and colleagues found frequent violations of discriminability, limited capacity, and informative-change principles across real presentations, and also found that untrained observers often failed to identify the design violations. See [“PowerPoint Presentation Flaws and Failures”](https://doi.org/10.3389/fpsyg.2012.00230).

The consequence is not one universal slide formula. It is a scenario-aware quality rule:

> Every element should help the intended audience perform the intended cognitive or organizational task in the intended delivery context.

---

## 8. What a PPT Is Not

A PPT is not inherently:

- A decorated document split into pages;
- A collection of attractive but unrelated canvases;
- A transcript of what the presenter will say;
- A visual effect showcase;
- A single-use slideshow with no afterlife;
- A flattened image that merely carries a `.pptx` extension;
- A template simply because its pages look consistent;
- The right medium for every communication task.

PowerPoint’s conventions can also distort communication when users start from default slide forms instead of the audience’s real task. The tool should serve the communication model; the communication model should not be reverse-engineered from the available buttons.

---

## 9. Questions Every PPT Request Should Answer

| Question | Why it matters |
|---|---|
| Who is the audience? | Determines language, assumed knowledge, evidence, and tone |
| What must change after they see it? | Defines the communication job and success condition |
| Is it presented, read, recorded, or mixed? | Determines density, typography, notes, and behavior |
| What is the central message? | Prevents slide construction before an argument exists |
| What evidence must be visible or traceable? | Protects factual integrity and decision usefulness |
| What may change and what must remain fixed? | Clarifies editing boundaries and review expectations |
| What must remain editable or native? | Defines object-model and delivery requirements |
| What will recur? | Determines whether a theme, master, layout, boilerplate, or no template is needed |

These questions should precede detailed decisions about style, layout, templates, animation, or authoring technique.

---

## 10. Sources and Further Reading

### PowerPoint and standards

- Microsoft Support: [What is PowerPoint?](https://support.microsoft.com/en-us/powerpoint/training/what-is-powerpoint)
- Microsoft Support: [Choose the right view for the task in PowerPoint](https://support.microsoft.com/en-US/PowerPoint/training/choose-the-right-view-for-the-task-in-powerpoint)
- Microsoft Support: [What is a slide layout?](https://support.microsoft.com/en-US/PowerPoint/what-is-a-slide-layout)
- Microsoft Support: [Understand the difference between PowerPoint templates and themes](https://support.microsoft.com/en-us/powerpoint/understand-the-difference-between-powerpoint-templates-and-themes)
- Microsoft Learn: [Structure of a PresentationML document](https://learn.microsoft.com/en-us/office/open-xml/presentation/structure-of-a-presentationml-document)
- Ecma International: [ECMA-376 Office Open XML File Formats](https://ecma-international.org/publications-and-standards/standards/ecma-376/)

### Communication and cognition

- Yates and Orlikowski: [Genres of Organizational Communication](https://doi.org/10.5465/amr.1992.4279545)
- Richard E. Mayer: [Multimedia Learning](https://www.cambridge.org/highereducation/books/multimedia-learning/FB7E79A165D24D47CEACEB4D2C426ECD)
- Bartsch and Cobern: [Effectiveness of PowerPoint presentations in lectures](https://doi.org/10.1016/S0360-1315(03)00027-7)
- Kosslyn et al.: [PowerPoint Presentation Flaws and Failures: A Psychological Analysis](https://doi.org/10.3389/fpsyg.2012.00230)
