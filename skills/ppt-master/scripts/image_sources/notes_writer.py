from pathlib import Path


HEADING = "Image Credits"


def append_image_credits(note_path, lines):
    note_file = Path(note_path)
    note_file.parent.mkdir(parents=True, exist_ok=True)

    normalized_lines = []
    for line in lines:
        text = str(line).strip()
        if not text:
            continue
        if not text.startswith("- "):
            text = f"- {text}"
        normalized_lines.append(text)

    if not normalized_lines:
        return note_file

    existing = ""
    if note_file.exists():
        existing = note_file.read_text(encoding="utf-8")

    chunks = []
    if existing:
        chunks.append(existing.rstrip())

    if HEADING not in existing:
        if chunks:
            chunks.append("")
        chunks.append(HEADING)

    chunks.extend(normalized_lines)
    note_file.write_text("\n".join(chunks) + "\n", encoding="utf-8")
    return note_file
