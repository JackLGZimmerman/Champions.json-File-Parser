from __future__ import annotations

import sys
from pathlib import Path


def main() -> None:
    project_src = Path(__file__).resolve().parents[1] / "src"
    if str(project_src) not in sys.path:
        sys.path.insert(0, str(project_src))

    from collect import main as collect_main

    collect_main()


if __name__ == "__main__":
    main()
