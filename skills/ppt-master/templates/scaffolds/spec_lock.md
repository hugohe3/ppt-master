<!-- ppt-master-schema: spec-lock/v1 -->
# Execution Lock

## canvas
- viewBox: {{VIEWBOX}}
- format: {{CANVAS_NAME}}

## communication
- audience:
- communication_intent:
- audience_outcome:
- core_message:
- delivery_context:
- artifact_afterlife:
- consumption_mode: [fill]

## mode
- mode: [fill]

## visual_style
- visual_style: [fill]

## colors
- bg: [fill]
- primary: [fill]
- accent: [fill]
- text: [fill]

## typography
- font_family: [fill]
- body: [fill]
- title: [fill]

## icons
- library: [fill]
- inventory: [fill]

## page_rhythm
- P01: [fill]

## pptx_structure
- mode: flat

## forbidden
- Mixing icon libraries
- `mask`, `<style>`, `class`, external CSS, `<foreignObject>`, `textPath`, `@font-face`, `<animate*>`, `<set>`, `<script>` / event attributes, `<iframe>`
- HTML named entities in text; write typography as raw Unicode and escape XML reserved characters
