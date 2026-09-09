#!/usr/bin/env python3
"""Stage only explicitly public, tracked website/download files for GitHub Pages."""

from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "_site"
ROOT_FILES = {
    "index.html",
    ".nojekyll",
    "README.md",
    "AUTHORS.md",
    "CITATION.cff",
    "LICENSE",
    "DATA_LICENSE.md",
    "THIRD_PARTY_NOTICES.md",
    "CHANGELOG.md",
    "checksums.sha256",
    "release_manifest.json",
    "validation_report.json",
    "browser_qa_report.json",
}
FOLDERS = {"assets", "web", "data", "docs", "research"}


def main():
    if DEST.exists():
        shutil.rmtree(DEST)
    DEST.mkdir()
    tracked = (
        subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT)
        .decode()
        .split("\0")
    )
    count = 0
    for name in tracked:
        p = Path(name)
        if not name or not (name in ROOT_FILES or p.parts[0] in FOLDERS):
            continue
        if any(
            x in {".git", "node_modules", "__pycache__", ".venv", ".DS_Store"}
            for x in p.parts
        ):
            raise ValueError(f"Disallowed tracked file: {name}")
        source = ROOT / p
        if source.is_symlink() or not source.is_file():
            raise ValueError(f"Invalid public file: {name}")
        target = DEST / p
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        count += 1
    if not (DEST / "index.html").exists():
        raise RuntimeError("No index staged")
    print(f"Staged {count} public files")


if __name__ == "__main__":
    main()
