"""Delete generated run artifacts under output/ after listing and confirmation."""

import shutil
import sys
from pathlib import Path


def main() -> int:
    root = Path("output")
    if root.is_symlink():
        print("output/ is a symlink; refusing to clean it", file=sys.stderr)
        return 1
    if not root.is_dir():
        print("Nothing to clean: output/ does not exist")
        return 0
    items = sorted(root.iterdir())
    if not items:
        print("output/ is already empty")
        return 0
    for item in items:
        print(f"  {item}")
    if input(f"Delete these {len(items)} item(s) under output/? [y/N] ").strip().lower() != "y":
        print("Cancelled; nothing deleted")
        return 1
    for item in items:
        if item.is_dir() and not item.is_symlink():
            shutil.rmtree(item)
        else:
            item.unlink()
    print(f"Deleted {len(items)} item(s) under output/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
