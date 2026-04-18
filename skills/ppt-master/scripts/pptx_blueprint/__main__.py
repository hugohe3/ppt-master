"""Package-level entry point — enables `python3 -m pptx_blueprint <pptx>`."""

from .cli import main

if __name__ == '__main__':
    raise SystemExit(main())
