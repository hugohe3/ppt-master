# DrawingML preset geometry data provenance

## Apache POI notice

Apache POI

Copyright 2003-2025 The Apache Software Foundation

This product includes software developed at

The Apache Software Foundation (<https://www.apache.org/>).

## Vendored data

`presetShapeDefinitions.xml` is vendored from Apache POI 5.4.1:

- Release tag: `REL_5_4_1`
- Source commit: `4554f204cbbf00ecbcaed134fe57e43a1779a612`
- Source path: `poi/src/main/resources/org/apache/poi/sl/draw/geom/presetShapeDefinitions.xml`
- Source revision: <https://github.com/apache/poi/tree/4554f204cbbf00ecbcaed134fe57e43a1779a612>
- Original release-file SHA-256:
  `a7dad593d27bd70536b41da9b761fa16409536cc0c25ef2b6c7a61c5d9b3e738`
- Vendored SHA-256: `4a762444d8d85876881c02a5b1dedf6f73006fcd8acb7b4e393435615b37c780`
- Modification: line endings normalized from the release JAR's mixed CRLF/LF to LF; XML content is otherwise unchanged.
- License: Apache License 2.0; see `LICENSE-APACHE-2.0.txt`.

The independent completeness list in `shape_type_values.txt` is derived from
the Open XML SDK schema metadata for `a:ST_ShapeType` / `ShapeTypeValues`:

- Repository: `dotnet/Open-XML-SDK`
- Source commit: `00967dc871f06776ae969762c6703d062308a6c9`
- Source path: `data/schemas/schemas_openxmlformats_org_drawingml_2006_main.json`
- Source revision:
  <https://github.com/dotnet/Open-XML-SDK/tree/00967dc871f06776ae969762c6703d062308a6c9>
- Source-file SHA-256:
  `e760b534c96ee02745d2a8084f1be362826da4470a85d0b0102a67c3b1678ab7`
- Vendored enum-list SHA-256:
  `f2c3bdcda8569b358ce3196cfeb183849e33bfc7955fac961dc85fceb6b3b587`
- License: MIT (`dotnet/Open-XML-SDK`); see
  `LICENSE-OPEN-XML-SDK-MIT.txt`.

At the locked revisions, both sources contain exactly 187 unique preset names,
and their sets are identical.

## Evaluator compatibility notes

- The circular-arrow, left-circular-arrow, and left-right-circular-arrow
  definitions each contain `+- xH 0 dxB 0`. Apache POI evaluates the first
  three operands and ignores the inert final zero. The PPT Master evaluator
  accepts only this trailing-zero compatibility form; other arity mismatches
  remain errors.
- A small number of definitions rebind an intermediate guide name later in
  the ordered `gdLst`. Evaluation therefore preserves document order and the
  later value replaces the earlier value, matching Apache POI behavior.
