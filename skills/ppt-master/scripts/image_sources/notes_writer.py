from pathlib import Path


HEADING = "Image Credits"


def normalize_credit_lines(lines):
    normalized_lines = []
    seen = set()

    for line in lines:
        text = str(line).strip()
        if not text:
            continue
        if not text.startswith("- "):
            text = f"- {text}"
        if text in seen:
            continue
        seen.add(text)
        normalized_lines.append(text)

    return normalized_lines


def split_image_credits(note_text):
    text = str(note_text or "")
    if not text:
        return "", []

    lines = text.splitlines()
    heading_index = None
    for index, line in enumerate(lines):
        if line.strip() == HEADING:
            heading_index = index
            break

    if heading_index is None:
        return text.rstrip(), []

    body = "\n".join(lines[:heading_index]).strip()
    credit_lines = normalize_credit_lines(lines[heading_index + 1 :])
    return body, credit_lines


def append_image_credits(note_path, lines):
    note_file = Path(note_path)
    note_file.parent.mkdir(parents=True, exist_ok=True)

    normalized_lines = normalize_credit_lines(lines)

    if not normalized_lines:
        return note_file

    existing_body = ""
    existing_credit_lines = []
    if note_file.exists():
        existing_body, existing_credit_lines = split_image_credits(
            note_file.read_text(encoding="utf-8")
        )

    merged_credit_lines = normalize_credit_lines(
        existing_credit_lines + normalized_lines
    )

    chunks = []
    if existing_body:
        chunks.append(existing_body.rstrip())

    if merged_credit_lines:
        if chunks:
            chunks.append("")
        chunks.append(HEADING)
        chunks.extend(merged_credit_lines)

    note_file.write_text("\n".join(chunks) + "\n", encoding="utf-8")
    return note_file
