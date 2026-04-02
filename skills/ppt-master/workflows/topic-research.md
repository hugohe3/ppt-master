---
description: Research a topic from scratch when the user provides only a brief description or requirements without detailed source materials. Produces a structured Markdown document and a folder of related images.
---

# Topic Research Workflow

> **Standalone pre-processing workflow** — produces source materials that can feed into the main PPT generation pipeline or be used independently.

## Trigger Condition

The user provides **only a topic name, a brief description, or a set of requirements** — no PDF, DOCX, URL, or other source files.

Examples:
- "Make a PPT about Joe Hisaishi"
- "Create a presentation about renewable energy trends"
- "I want to introduce our new product (with a brief description)"

## Deliverables

All outputs MUST be placed under the `projects/` directory:

| Deliverable | Path | Example |
|-------------|------|---------|
| Structured Markdown document | `projects/<topic_name>.md` | `projects/joe_hisaishi.md` |
| Image folder | `projects/<topic_name>/` (same name as the document, without extension) | `projects/joe_hisaishi/` |

> **Naming consistency rule**: The Markdown filename (without `.md`) and the image folder name MUST be identical.
>
> **Output directory rule**: Both the document and image folder MUST be created inside `projects/`. Never place them in the repository root or any other location.

## Process Overview

```
Confirm Topic → Research Content → Collect Images → Output
```

---

## Step 1: Topic Confirmation

⛔ **BLOCKING**: Before starting research, confirm the following with the user. If the user's initial message already covers these points clearly, skip the confirmation and proceed.

| Item | Description | Example |
|------|-------------|---------|
| **Topic** | Core subject | Joe Hisaishi |
| **Scope / Focus** | What aspects to cover | Biography, major works, collaboration with Miyazaki, awards |
| **Depth** | Surface overview vs. deep dive | General knowledge level |
| **Language** | Output language | English |

**If the user's request is already clear enough** (e.g., "Make a PPT about Joe Hisaishi"), infer reasonable defaults and proceed — do not over-ask.

---

## Step 2: Content Research

### 2.1 Information Gathering

Use `WebSearch` and `WebFetch` to collect information from multiple sources:

| Source Type | Priority | Tools | Notes |
|------------|----------|-------|-------|
| Wikipedia / Encyclopedia | High | WebSearch → WebFetch | Authoritative overview, timeline, key facts |
| Official websites | High | WebFetch | First-party information |
| News / media articles | Medium | WebSearch → WebFetch | Recent events, awards, public reception |
| Professional databases | Low | WebSearch | Industry-specific data if relevant |

**Research strategy**:
1. Start with a broad WebSearch to understand the topic landscape
2. WebFetch 2-3 key authoritative pages (Wikipedia, official sites) for detailed content
3. Supplement with targeted searches for specific subtopics as needed

### 2.2 Content Organization

Organize the gathered information into a structured Markdown document with the following skeleton:

```markdown
# <Topic Name>

> Brief one-line description of the topic.

## Overview
[2-3 paragraph summary]

## Background / History
[Timeline, origin story, key milestones]

## Key Aspects
### Aspect 1: [...]
### Aspect 2: [...]
### Aspect 3: [...]

## Achievements / Impact
[Awards, recognition, influence]

## Key Facts & Figures
| Item | Value |
|------|-------|
| ... | ... |

## Sources
- [Source 1 title](URL)
- [Source 2 title](URL)
```

> The skeleton above is a **reference template** — adapt the section structure to fit the topic. A person biography will differ from a technology overview or a company profile.

**Content guidelines**:
- Include specific facts, dates, and names — avoid vague generalizations
- Preserve key quotes when found
- Note data sources for verifiability
- Aim for PPT-ready content density: enough detail to fill 10-15 slides, but not an exhaustive research paper

### 2.3 Save Document

Save the Markdown document to the `projects/` directory:

```
projects/<topic_name>.md
```

---

## Step 3: Image Collection

### 3.1 Image Source Strategy

Search for **publicly available, freely usable** images in this priority order:

| Source | How to Find | License Notes |
|--------|------------|---------------|
| **Wikipedia / Wikimedia Commons** | WebFetch the Wikipedia page → extract `upload.wikimedia.org` image URLs → get full-resolution versions (remove `/thumb/` and size suffix from URL) | CC-BY-SA or Public Domain |
| **Official websites** | WebFetch official/institutional pages → look for gallery or press sections | Typically free for editorial/educational use |
| **Government / institutional releases** | WebSearch for official press kits, public galleries | Usually public domain |
| **Creative Commons search** | WebSearch with `site:commons.wikimedia.org` or `site:flickr.com/photos` + creative commons | Check specific CC license |

**Avoid**: Stock photo sites with watermarks, copyrighted commercial images, social media uploads without clear licensing.

### 3.2 Image Selection Criteria

| Criterion | Guideline |
|-----------|-----------|
| **Quantity** | 6-12 images (enough to support a 10-15 page PPT) |
| **Variety** | Mix of portraits, scenes, logos, event photos as relevant |
| **Resolution** | Prefer 1000px+ width; avoid thumbnails |
| **Relevance** | Each image should serve a clear purpose (cover, illustration, background) |
| **Aspect ratio mix** | Include both landscape (for backgrounds) and portrait (for profiles) when applicable |

### 3.3 Download Process

```bash
# Create image folder under projects/ (same name as the document)
mkdir -p "projects/<topic_name>"

# Download images with descriptive filenames
curl -L -o "projects/<topic_name>/descriptive_name.jpg" "<image_url>"
```

**Filename rules**:
- Use descriptive English names: `joe_hisaishi_concert.jpg`, not `image1.jpg`
- Lowercase, underscores for spaces
- Include subject and context: `spirited_away_poster.jpg`, `tokyo_concert_2023.jpg`

### 3.4 Full-Resolution URL Patterns

Common patterns for getting full-resolution images from known sources:

| Source | Thumbnail URL | Full-Resolution URL |
|--------|--------------|---------------------|
| Wikimedia | `.../thumb/a/ab/File.jpg/250px-File.jpg` | `.../a/ab/File.jpg` (remove `thumb/` and `/250px-File.jpg`) |
| Ghibli official | `www.ghibli.jp/gallery/thumb-xxx.png` | `www.ghibli.jp/gallery/xxx.jpg` |

---

## Step 4: Output Summary

After completing Steps 2 and 3, output a brief summary:

```markdown
## Topic Research Complete

**Topic**: <topic_name>
**Document**: `projects/<topic_name>.md` — [X sections, approximately Y words]
**Images**: `projects/<topic_name>/` — [N images collected]

| Filename | Source | Description |
|----------|--------|-------------|
| ... | ... | ... |
```

> From here, the user or main pipeline can use these materials as input for PPT generation (import via `project_manager.py import-sources` or read directly).

---

## Notes

- This workflow is **content-gathering only** — it does not create a PPT project, generate SVGs, or produce a design spec
- The Markdown document should be **PPT-ready**: well-structured, factual, with clear sections that map naturally to presentation slides
- Always include a **Sources** section in the Markdown for attribution and verifiability
- When a topic is well-known (e.g., a famous person, a major technology), 2-3 WebSearch + WebFetch rounds are usually sufficient; avoid over-researching
- For niche topics, more extensive searching may be needed — use judgment
