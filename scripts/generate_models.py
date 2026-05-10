"""Regenerate xsdata Pydantic models from vendored ISO 20022 XSDs.

xsdata resolves the <Package> config relative to the current working
directory. Running it from src/ ensures output lands in
src/pactus/generated/ rather than ./pactus/generated/ at the repo root.

Usage:
    uv run python scripts/generate_models.py
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    src_dir = repo_root / "src"
    schemas_dir_relative = Path("pactus") / "schemas"
    output_dir = src_dir / "pactus" / "generated"

    if not (src_dir / schemas_dir_relative).is_dir():
        print(
            f"error: schemas directory not found at {src_dir / schemas_dir_relative}",
            file=sys.stderr,
        )
        return 1

    # Wipe previous generation output, but preserve .gitkeep so the
    # directory exists in git (even though *.py files are gitignored).
    if output_dir.is_dir():
        for child in output_dir.iterdir():
            if child.name == ".gitkeep":
                continue
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()

    # xsdata reads .xsdata.xml from CWD. We cd to src/ so that
    # <Package>pactus.generated</Package> resolves to src/pactus/generated/.
    config_src = repo_root / ".xsdata.xml"
    config_dest = src_dir / ".xsdata.xml"
    shutil.copy2(config_src, config_dest)
    try:
        result = subprocess.run(
            ["uv", "run", "xsdata", "generate", str(schemas_dir_relative)],
            cwd=src_dir,
            check=False,
        )
    finally:
        config_dest.unlink(missing_ok=True)

    if result.returncode != 0:
        print(f"error: xsdata generate exited with {result.returncode}", file=sys.stderr)
        return result.returncode

    generated_files = sorted(output_dir.glob("*.py"))
    print(f"\ngenerated {len(generated_files)} files in {output_dir.relative_to(repo_root)}:")
    for f in generated_files:
        print(f"  {f.name} ({f.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
