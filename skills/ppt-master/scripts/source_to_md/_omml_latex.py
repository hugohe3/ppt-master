#!/usr/bin/env python3
"""
PPT Master - Office Math (OMML) to LaTeX

Convert one OMML subtree to a LaTeX string for the source converters, so Word
and PowerPoint equations reach the Markdown as `$...$` / `$$...$$`.

Usage:
    Imported by scripts/source_to_md/doc_to_md.py and ppt_to_md.py

Examples:
    _omml_to_latex(o_math_element)

Dependencies:
    None
"""

from __future__ import annotations

from xml.etree import ElementTree as ET

MATH_NS = "http://schemas.openxmlformats.org/officeDocument/2006/math"

# OMML n-ary operator chars (m:nary/m:naryPr/m:chr) → LaTeX command.
NARY_OPS = {
    "∑": r"\sum", "∏": r"\prod", "∐": r"\coprod",
    "∫": r"\int", "∬": r"\iint", "∭": r"\iiint", "∮": r"\oint",
    "⋃": r"\bigcup", "⋂": r"\bigcap", "⋁": r"\bigvee", "⋀": r"\bigwedge",
}
# OMML accent chars (m:acc/m:accPr/m:chr) → LaTeX command.
ACCENT_CMDS = {
    "̂": r"\hat", "̃": r"\tilde", "̄": r"\bar", "→": r"\vec", "⃗": r"\vec",
    "̇": r"\dot", "̈": r"\ddot", "̌": r"\check", "́": r"\acute", "̀": r"\grave",
}


def _local_name(elem: ET.Element) -> str:
    """Return an element's local name; lxml comments and PIs have none."""
    tag = elem.tag
    return tag.rsplit("}", 1)[-1] if isinstance(tag, str) else ""


def _m_child(elem: ET.Element, name: str) -> ET.Element | None:
    """Return the first OMML child with the given local name."""
    for child in elem:
        if _local_name(child) == name:
            return child
    return None


def _m_pr_val(elem: ET.Element, prop: str) -> str | None:
    """Return m:val of a property inside the element's *Pr block (e.g. chr)."""
    for child in elem:
        if not _local_name(child).endswith("Pr"):
            continue
        for sub in child:
            if _local_name(sub) == prop:
                return sub.get(f"{{{MATH_NS}}}val")
    return None


def _brace(latex: str) -> str:
    """Wrap multi-char LaTeX in braces so it binds as one super/subscript arg."""
    return latex if len(latex) <= 1 else "{" + latex + "}"


def _omml_part(elem: ET.Element, name: str) -> str:
    """Convert a named OMML child (e/num/den/sup/sub/...) to LaTeX."""
    child = _m_child(elem, name)
    return _omml_to_latex(child) if child is not None else ""


def _omml_run(elem: ET.Element) -> str:
    """Concatenate text from an OMML run, skipping property children."""
    return "".join(
        c.text or "" for c in elem if _local_name(c) == "t"
    )


def _omml_children(elem: ET.Element) -> str:
    """Convert all non-property children in order (default/passthrough rule)."""
    return "".join(
        _omml_to_latex(c) for c in elem if not _local_name(c).endswith("Pr")
    )


def _omml_matrix(elem: ET.Element, *, environment: str) -> str:
    """Convert a matrix (m:m) or equation array (m:eqArr) to a LaTeX env."""
    rows: list[str] = []
    for row in elem:
        if _local_name(row) not in ("mr", "e"):
            continue
        if _local_name(row) == "e":  # eqArr stores rows as bare <m:e>
            rows.append(_omml_to_latex(row))
            continue
        cells = [_omml_to_latex(cell) for cell in row if _local_name(cell) == "e"]
        rows.append(" & ".join(cells))
    body = r" \\ ".join(rows)
    return rf"\begin{{{environment}}} {body} \end{{{environment}}}"


def _omml_to_latex(elem: ET.Element) -> str:
    """Recursively convert one OMML element subtree to a LaTeX string.

    Unknown elements degrade to a concatenation of their children rather than
    being dropped, so rare constructs lose markup but never lose content.
    """
    local = _local_name(elem)

    if local == "t":
        return elem.text or ""
    if local == "r":
        return _omml_run(elem)
    if local in ("oMath", "oMathPara", "e", "num", "den", "sup", "sub",
                 "deg", "fName", "lim", "box", "borderBox"):
        return _omml_children(elem)
    if local == "sSup":
        return _brace(_omml_part(elem, "e")) + "^" + _brace(_omml_part(elem, "sup"))
    if local == "sSub":
        return _brace(_omml_part(elem, "e")) + "_" + _brace(_omml_part(elem, "sub"))
    if local == "sSubSup":
        return (_brace(_omml_part(elem, "e"))
                + "_" + _brace(_omml_part(elem, "sub"))
                + "^" + _brace(_omml_part(elem, "sup")))
    if local == "sPre":
        return ("{}_" + _brace(_omml_part(elem, "sub"))
                + "^" + _brace(_omml_part(elem, "sup"))
                + _brace(_omml_part(elem, "e")))
    if local == "f":
        return r"\frac{" + _omml_part(elem, "num") + "}{" + _omml_part(elem, "den") + "}"
    if local == "rad":
        deg = _m_child(elem, "deg")
        body = _omml_part(elem, "e")
        deg_latex = _omml_to_latex(deg) if deg is not None and len(deg) else ""
        return rf"\sqrt[{deg_latex}]{{{body}}}" if deg_latex else rf"\sqrt{{{body}}}"
    if local == "d":
        beg = _m_pr_val(elem, "begChr")
        end = _m_pr_val(elem, "endChr")
        beg = "(" if beg is None else (beg or ".")
        end = ")" if end is None else (end or ".")
        separator = _m_pr_val(elem, "sepChr")
        separator = "|" if separator is None else separator
        separator = _latex_literal(separator)
        beg = {"{": r"\{", "}": r"\}"}.get(beg, beg)
        end = {"{": r"\{", "}": r"\}"}.get(end, end)
        inner = separator.join(_omml_to_latex(c) for c in elem if _local_name(c) == "e")
        return rf"\left{beg}{inner}\right{end}"
    if local == "nary":
        chr_ = _m_pr_val(elem, "chr") or "∫"
        op = NARY_OPS.get(chr_, chr_)
        sub, sup = _m_child(elem, "sub"), _m_child(elem, "sup")
        out = op
        if sub is not None and len(sub):
            out += "_" + _brace(_omml_to_latex(sub))
        if sup is not None and len(sup):
            out += "^" + _brace(_omml_to_latex(sup))
        return out + _brace(_omml_part(elem, "e"))
    if local == "func":
        return "\\" + _omml_part(elem, "fName").strip() + _brace(_omml_part(elem, "e"))
    if local == "limLow":
        return _brace(_omml_part(elem, "e")) + "_" + _brace(_omml_part(elem, "lim"))
    if local == "limUpp":
        return _brace(_omml_part(elem, "e")) + "^" + _brace(_omml_part(elem, "lim"))
    if local == "bar":
        cmd = r"\underline" if _m_pr_val(elem, "pos") == "bot" else r"\overline"
        return cmd + "{" + _omml_part(elem, "e") + "}"
    if local == "acc":
        cmd = ACCENT_CMDS.get(_m_pr_val(elem, "chr") or "̂", r"\hat")
        return cmd + "{" + _omml_part(elem, "e") + "}"
    if local == "groupChr":
        char = _m_pr_val(elem, "chr")
        char = "⏟" if char is None else char
        pos = _m_pr_val(elem, "pos") or "bot"
        body = _omml_part(elem, "e")
        if (char, pos) in {("⏞", "top"), ("⏟", "bot")}:
            cmd = r"\overbrace" if pos == "top" else r"\underbrace"
            return cmd + "{" + body + "}"
        cmd = r"\overset" if pos == "top" else r"\underset"
        return cmd + r"{\text{" + _latex_literal(char) + "}}{" + body + "}"
    if local == "m":
        return _omml_matrix(elem, environment="matrix")
    if local == "eqArr":
        return _omml_matrix(elem, environment="aligned")

    return _omml_children(elem)


def _latex_literal(text: str) -> str:
    """Escape literal characters that would otherwise change LaTeX syntax."""
    escapes = {"\\": r"\backslash{}", "{": r"\{", "}": r"\}", "%": r"\%",
               "&": r"\&", "#": r"\#", "_": r"\_", "$": r"\$"}
    return "".join(escapes.get(char, char) for char in text)
