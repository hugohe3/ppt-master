## Directory Overview

This directory contains the "PPT Master" project, an AI-driven system for generating high-quality SVG presentations. It is a non-code project, meaning it doesn't contain source code that needs to be compiled or run. Instead, it provides a structured framework of roles, examples, and documentation to guide AI agents in the presentation creation process.

The core idea is to use a series of specialized AI "roles" to transform a source document into a professional-looking SVG presentation, mimicking the workflow of a design agency.

## Key Files

*   `README.md`: The main entry point for understanding the project. It provides a comprehensive overview of the system, its architecture, the different AI roles, and a quick start guide.
*   `roles/`: This directory contains the detailed definitions for the four AI roles:
    *   `Strategist.md`: The first role, responsible for analyzing the source document, communicating with the user (providing professional suggestions for page count, audience, and style), and creating a design brief.
    *   `Executor_General.md`: The role that generates SVG slides in a "general flexible style".
    *   `Executor_Consultant.md`: The role that generates SVG slides in a "high-end consulting style".
    *   `Optimizer_CRAP.md`: The role that refines and optimizes the visual design of the generated SVGs based on the CRAP design principles (Contrast, Repetition, Alignment, Proximity).
*   `examples/`: This directory contains multiple project-based examples, each with its own folder.
    *   `<project_name>_<format>_<YYYYMMDD>/`: A complete example project (e.g., `重庆汇丰尽职调查_PPT_20251015`).
        *   `设计规范与内容大纲.md`/`design_specification.md`: The Strategist's design brief.
        *   `svg_output/`: The generated SVG slides.
        *   `preview.html` (optional): A simple preview entry.
*   `docs/`: This directory contains additional documentation:
    *   `design_guidelines.md`: Detailed design guidelines for creating presentations.
    *   `workflow_tutorial.md`: A tutorial on how to use the system.
    *   `quick_reference.md`: A quick reference guide.

## Usage

This project is intended to be used with a large language model (LLM) that can understand and follow the instructions laid out in the role definition files. The workflow is as follows:

1.  **Provide a source document:** Start with a text document that contains the content for the presentation.
2.  **Engage the "Strategist" AI:** Use the `Strategist.md` file as a prompt for the LLM to analyze the source document and create a design brief. This involves a dialogue with the AI where:
    - **The Strategist will confirm four items** (page range, audience/scenario, style preference, canvas format)
    - **The Strategist will provide professional suggestions** for each item based on content analysis
    - The user can accept the suggestions or propose adjustments
3.  **Engage an "Executor" AI:** Based on the desired style, use either `Executor_General.md` or `Executor_Consultant.md` as a prompt for the LLM to generate the SVG code for each slide.
4.  **(Optional) Engage the "Optimizer" AI:** If desired, use the `Optimizer_CRAP.md` file as a prompt for the LLM to refine the visual design of the generated slides.

### Optional post-process: Flatten `<tspan>`

At generation time, use `<tspan>` for manual line breaks (no `<foreignObject>`). If your pipeline requires plain `<text>` nodes for rendering or text extraction, run:

```bash
python3 tools/flatten_tspan.py examples/<project_name>_<format>_<YYYYMMDD>/svg_output
# or a single file
python3 tools/flatten_tspan.py path/to/input.svg path/to/output.svg
```

This writes a `svg_output_flattext` directory by default and should preserve visual styling/positions while removing `<tspan>`.
