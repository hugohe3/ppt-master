import re
import ast
import pathlib
import sys


def main():
    tree = ast.parse(pathlib.Path("cli.py").read_text())
    commands = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Dict):
            keys = [k.value for k in node.keys if isinstance(k, ast.Constant)]
            vals = [v.value for v in node.values if isinstance(v, ast.Constant)]
            if "project" in keys and "project_manager.py" in vals:
                commands = dict(zip(keys, vals))
                break

    if not commands:
        print("ERROR: Could not parse COMMANDS dict from cli.py", file=sys.stderr)
        return 1

    script_to_cmd = {}
    for cmd_name, script_rel in commands.items():
        script_name = script_rel.replace("\\", "/").split("/")[-1]
        script_to_cmd[script_name] = cmd_name

    exclude = ["superpowers", "windows-installation", "code-style", "upstream-sync"]
    root = pathlib.Path(".")
    targets = list(root.glob("skills/ppt-master/**/*.md"))
    targets += [root / "AGENTS.md", root / "CLAUDE.md"]
    targets += [f for f in root.glob("docs/**/*.md") if not any(k in str(f) for k in exclude)]
    targets += list(root.glob("projects/**/*.md"))

    fixed = 0
    for fp in sorted(set(targets)):
        if not fp.exists():
            continue
        try:
            content = fp.read_text()
        except Exception:
            print(f"WARNING: Could not read {fp}", file=sys.stderr)
            continue
        original = content
        for script_name, cmd_name in sorted(script_to_cmd.items()):
            p = re.escape(script_name)
            content = re.sub(rf"python3\s+skills/ppt-master/scripts/(\S*/)?{p}", f"uvx ppt-master {cmd_name}", content)
            content = re.sub(rf"(?<!\w)python3\s+scripts/(\S*/)?{p}", f"uvx ppt-master {cmd_name}", content)
            content = re.sub(rf"uv\s+run\s+skills/ppt-master/scripts/(\S*/)?{p}", f"uvx ppt-master {cmd_name}", content)
            content = re.sub(rf"(?<!\w)uv\s+run\s+scripts/(\S*/)?{p}", f"uvx ppt-master {cmd_name}", content)
        if content != original:
            try:
                fp.write_text(content)
                fixed += 1
                print(f"Fixed: {fp}")
            except Exception:
                print(f"ERROR: Could not write {fp}", file=sys.stderr)
                return 1

    print(f"Total files auto-fixed: {fixed}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
