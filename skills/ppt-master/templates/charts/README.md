# SVG Visualization Template Library (57 Types)

This directory provides **57 standardized SVG visualization templates** for use as structured visualization selection references in PPT Master.

> For backward compatibility, the directory remains `templates/charts/`, but the library scope includes charts, infographics, process diagrams, relationship diagrams, and strategic frameworks.

- **Full Index**: [README.md](./README.md) (human browsing)
- **JSON Index**: [charts_index.json](./charts_index.json) (AI / programmatic lookup — preferred)

Before generating chart pages, review the corresponding template file to understand its structure and layout.

## Quick Selection

> **AI / Programmatic recommendation**: Prefer reading `charts_index.json`; use this README for human browsing and quick comparison.

| I want to show... | Recommended Visualization | Filename |
|-------------------|---------------------------|----------|
| Key numeric metrics | KPI Cards | `kpi_cards.svg` |
| Category value comparison | Bar Chart | `bar_chart.svg` |
| Long-label rankings | Horizontal Bar Chart | `horizontal_bar_chart.svg` |
| Multi-series comparison | Grouped Bar Chart | `grouped_bar_chart.svg` |
| Time trends | Line Chart | `line_chart.svg` |
| Cumulative trends | Area Chart | `area_chart.svg` |
| Proportional composition | Pie / Donut Chart | `pie_chart.svg` / `donut_chart.svg` |
| Goal completion rate | Progress Bar / Gauge | `progress_bar_chart.svg` / `gauge_chart.svg` |
| Conversion funnel | Funnel Chart | `funnel_chart.svg` |
| Project scheduling | Gantt Chart | `gantt_chart.svg` |
| Milestone events | Timeline | `timeline.svg` |
| Multi-dimensional assessment | Radar Chart | `radar_chart.svg` |
| Bidirectional comparison | Butterfly Chart | `butterfly_chart.svg` |
| Incremental breakdown | Waterfall Chart | `waterfall_chart.svg` |
| Flow / fund allocation | Sankey Chart | `sankey_chart.svg` |
| Strategic analysis | SWOT / Porter's Five Forces | `swot_analysis.svg` / `porter_five_forces.svg` |
| Quadrant analysis | Matrix (2x2) | `matrix_2x2.svg` |

## Full Visualization Index

### Comparison

| Filename | Purpose | Use Cases |
|----------|---------|-----------|
| `bar_chart.svg` | Vertical bar comparison (3-8 bars) | Sales comparison, regional ranking |
| `horizontal_bar_chart.svg` | Horizontal bar ranking (5-12 bars) | Brand ranking, satisfaction scores |
| `grouped_bar_chart.svg` | Multi-series grouped comparison | Quarterly product line comparison, YoY/QoQ |
| `stacked_bar_chart.svg` | Stacked composition comparison | Revenue composition, market share changes |
| `butterfly_chart.svg` | Bidirectional comparison | Population pyramid, A/B testing, income vs expense |
| `bullet_chart.svg` | Target vs actual | KPI achievement, performance evaluation |
| `dumbbell_chart.svg` | Multi-dimension score comparison | Competitive analysis, composite index |
| `waterfall_chart.svg` | Incremental change breakdown | Profit decomposition, budget variance |

### Trends

| Filename | Purpose | Use Cases |
|----------|---------|-----------|
| `line_chart.svg` | Line trend (multi-line support) | Time series, growth trends |
| `area_chart.svg` | Area cumulative trend | Traffic trends, user growth |
| `stacked_area_chart.svg` | Multi-series stacked trend | Revenue sources, traffic source changes |
| `dual_axis_line_chart.svg` | Dual Y-axis different-unit comparison | Sales vs profit margin, traffic vs conversion rate |

### Proportions

| Filename | Purpose | Use Cases |
|----------|---------|-----------|
| `pie_chart.svg` | Basic proportion (3-6 slices) | Market share, budget allocation |
| `donut_chart.svg` | Ring proportion (with center data) | Structural proportion, category composition |
| `treemap_chart.svg` | Hierarchical area proportion | Budget allocation, market share composition |

### Metrics

| Filename | Purpose | Use Cases |
|----------|---------|-----------|
| `kpi_cards.svg` | Key metric cards (2x2 / 1x4) | Financial overview, data dashboard |
| `gauge_chart.svg` | Gauge completion rate | KPI completion, performance monitoring |
| `progress_bar_chart.svg` | Multi-item progress bars | OKR progress, project completion |

### Analysis

| Filename | Purpose | Use Cases |
|----------|---------|-----------|
| `radar_chart.svg` | Multi-dimensional assessment (4-8 axes) | Capability assessment, competitive comparison |
| `scatter_chart.svg` | Correlation / distribution | Input-output analysis, price-demand |
| `funnel_chart.svg` | Conversion funnel (3-5 stages) | Sales funnel, user conversion |
| `matrix_2x2.svg` | Four-quadrant analysis | BCG matrix, priority analysis |
| `bubble_chart.svg` | 3D bubble (X/Y/Size) | Market size vs growth rate vs share |
| `heatmap_chart.svg` | Matrix heatmap | User activity periods, correlation matrix |
| `pareto_chart.svg` | 80/20 Pareto analysis | Quality attribution, sales contribution |
| `box_plot_chart.svg` | Box plot distribution | Salary distribution, quality control |

### Project Management / Relationships

| Filename | Purpose | Use Cases |
|----------|---------|-----------|
| `gantt_chart.svg` | Gantt schedule (6-12 tasks) | Project management, product roadmap |
| `timeline.svg` | Timeline events (3-8 nodes) | Milestones, historical evolution |
| `process_flow.svg` | Process flow steps | Business processes, operational guides |
| `org_chart.svg` | Org structure (2-4 levels) | Company structure, reporting relationships |
| `sankey_chart.svg` | Data flow (three-tier) | Budget flow, user conversion paths |

### Strategic Frameworks

| Filename | Purpose | Use Cases |
|----------|---------|-----------|
| `swot_analysis.svg` | SWOT four-quadrant analysis | Strategic planning, competitive analysis |
| `porter_five_forces.svg` | Porter's Five Forces model | Industry analysis, market entry assessment |

### System Architecture

Use this family when source content describes a system with named modules **and** per-module descriptions — not just labels. Each template forces "title + description" pairs per node, which is what the plain `org_chart` / `hub_spoke` / `process_flow` templates do not enforce.

| Filename | Purpose | Use Cases |
|----------|---------|-----------|
| `layered_architecture.svg` | 3-4 horizontal layers × 2-4 module cards per layer, each card with title + 1-line description | Technical stack overview, application/service/data layering |
| `module_composition.svg` | Parent container + 3-N child cards, each child with title + 2-3 bullet descriptions | "Feature X contains 3 parts, each has its own description" — the canonical composition case |
| `hub_with_described_spokes.svg` | Central core + 4-6 radiating cards, each spoke with capability name + 1-2 line description | Data platform capability matrix, core engine + peripheral services |
| `pipeline_with_stages.svg` | 3-5 horizontal stages, each stage with title + description + output artifact, arrows between | Data pipeline, ETL flow, build pipeline with named outputs |
| `client_server_flow.svg` | Left client group + right server group + labeled bidirectional arrows between | Request-response architecture, front/back-end interaction, C/S protocol stack |
