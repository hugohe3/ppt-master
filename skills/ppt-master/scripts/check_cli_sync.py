"""Verify all scripts in the scripts directory have a mapping in cli.py."""

import ast
import os
import sys

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(SCRIPTS_DIR)))
CLI_FILE = os.path.join(ROOT_DIR, "cli.py")


def find_scripts_with_main(scripts_dir: str) -> set[str]:
    """Find all .py files under scripts_dir that define a main() function."""
    scripts: set[str] = set()
    for root, dirs, files in os.walk(scripts_dir):
        dirs[:] = [d for d in dirs if not d.startswith("_") and d != "__pycache__"]
        for f in files:
            if not f.endswith(".py") or f.startswith("__"):
                continue
            path = os.path.join(root, f)
            try:
                with open(path, encoding="utf-8") as fh:
                    tree = ast.parse(fh.read())
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == "main":
                    rel = os.path.relpath(path, scripts_dir)
                    scripts.add(rel.replace("\\", "/"))
                    break
    return scripts


def parse_commands_from_cli(cli_path: str) -> set[str]:
    """Parse the COMMANDS dict from cli.py to extract script paths."""
    with open(cli_path, encoding="utf-8") as f:
        tree = ast.parse(f.read())
    scripts: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name) and target.id == "COMMANDS":
                if isinstance(node.value, ast.Dict):
                    for v in node.value.values:
                        if isinstance(v, ast.Constant):
                            scripts.add(v.value)
    return scripts


def derive_command_name(script_path: str) -> str:
    """Derive kebab-case command name from script file path."""
    basename = os.path.splitext(os.path.basename(script_path))[0]
    basename = basename.replace("_", "-")
    dirname = os.path.dirname(script_path)
    if dirname and dirname != ".":
        dirname = dirname.replace("_", "-").replace("\\", "/")
        if dirname == "source-to-md":
            return basename
    return basename


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv

    scripts = find_scripts_with_main(SCRIPTS_DIR)
    # Exclude this script itself and Flask helper modules (not CLI tools)
    scripts.discard("check_cli_sync.py")
    scripts.discard(os.path.join("svg_editor", "app.py"))
    # Exclude internal sub-scripts wrapped by parent commands
    #   svg_finalize/ — called by finalize-svg
    #   svg_to_pptx/pptx_cli.py — called by svg-to-pptx
    #   template_fill_pptx/cli.py — called by template-fill-pptx
    scripts = {s for s in scripts if not s.startswith("svg_finalize/")}
    scripts.discard("svg_to_pptx/pptx_cli.py")
    scripts.discard("template_fill_pptx/cli.py")

    if not os.path.exists(CLI_FILE):
        print(f"ERROR: cli.py not found at {CLI_FILE}", file=sys.stderr)
        return 1

    mapped = parse_commands_from_cli(CLI_FILE)

    missing = scripts - mapped
    if not missing:
        print("OK: All scripts have CLI mappings.")
        return 0

    print("ERROR: The following scripts are missing from cli.py COMMANDS dict:\n", file=sys.stderr)
    for script in sorted(missing):
        cmd = derive_command_name(script)
        print(f'    "{cmd}": "{script}",  # {cmd.replace("-", " ")}', file=sys.stderr)
    print(f"\nAdd the above entries to the COMMANDS dict in cli.py.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
