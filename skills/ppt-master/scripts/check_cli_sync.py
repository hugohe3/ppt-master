"""Verify all scripts in the scripts directory have a mapping in cli.py."""

import ast
import os
import sys

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(SCRIPTS_DIR)))
SKILL_DIR = os.path.join(ROOT_DIR, "skills", "ppt-master")
CLI_FILE = os.path.join(ROOT_DIR, "cli.py")
SKILL_CLI_FILE = os.path.join(SKILL_DIR, "cli.py")


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


def parse_commands_from_cli(cli_path: str) -> tuple[set[str], set[str]]:
    """Parse the COMMANDS dict from cli.py to extract (command_names, script_paths)."""
    with open(cli_path, encoding="utf-8") as f:
        tree = ast.parse(f.read())
    scripts: set[str] = set()
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name) and target.id == "COMMANDS":
                if isinstance(node.value, ast.Dict):
                    for k, v in zip(node.value.keys, node.value.values):
                        if isinstance(k, ast.Constant) and isinstance(v, ast.Constant):
                            names.add(k.value)
                            scripts.add(v.value)
    return names, scripts


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
    scripts.discard("check_uvx_migration.py")
    scripts.discard("svg_editor/app.py")
    scripts.discard("confirm_ui/server.py")
    # Exclude internal sub-scripts wrapped by parent commands
    #   svg_finalize/ — called by finalize-svg
    #   svg_to_pptx/pptx_cli.py — called by svg-to-pptx
    #   template_fill_pptx/cli.py — called by template-fill-pptx
    scripts = {s for s in scripts if not s.startswith("svg_finalize/")}
    scripts.discard("svg_to_pptx/pptx_cli.py")
    scripts.discard("svg_to_pptx/pptx_package/cli.py")
    scripts.discard("template_fill_pptx/cli.py")

    if not os.path.exists(CLI_FILE):
        print(f"ERROR: cli.py not found at {CLI_FILE}", file=sys.stderr)
        return 1

    root_names, mapped = parse_commands_from_cli(CLI_FILE)

    missing = scripts - mapped
    if missing:
        print("ERROR: The following scripts are missing from cli.py COMMANDS dict:\n", file=sys.stderr)
        for script in sorted(missing):
            cmd = derive_command_name(script)
            print(f'    "{cmd}": "{script}",  # {cmd.replace("-", " ")}', file=sys.stderr)
        print(f"\nAdd the above entries to the COMMANDS dict in cli.py.", file=sys.stderr)
        return 1

    print("OK: All scripts have CLI mappings in root cli.py.")

    # Check skill cli.py is in sync with root cli.py
    if os.path.exists(SKILL_CLI_FILE):
        skill_names, _ = parse_commands_from_cli(SKILL_CLI_FILE)
        if skill_names != root_names:
            missing_in_skill = root_names - skill_names
            missing_in_root = skill_names - root_names
            if missing_in_skill:
                print("ERROR: Commands in root cli.py missing from skills/ppt-master/cli.py:\n", file=sys.stderr)
                for name in sorted(missing_in_skill):
                    print(f"    {name}", file=sys.stderr)
            if missing_in_root:
                print("ERROR: Commands in skills/ppt-master/cli.py missing from root cli.py:\n", file=sys.stderr)
                for name in sorted(missing_in_root):
                    print(f"    {name}", file=sys.stderr)
            return 1
        print("OK: Both cli.py files are in sync.")
    else:
        print(f"WARNING: skills/ppt-master/cli.py not found at {SKILL_CLI_FILE}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
