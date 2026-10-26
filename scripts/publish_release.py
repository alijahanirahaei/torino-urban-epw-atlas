"""Create a release once, or verify existing downloads without replacing them."""
import argparse
from datetime import date
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED


def run(*args):
    return subprocess.check_output(args, text=True).strip()


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_tag(kind, tag, root):
    prefix = "v" if kind == "atlas" else "supplement-v"
    if not re.fullmatch(re.escape(prefix) + r"[0-9]+\.[0-9]+\.[0-9]+", tag):
        raise ValueError("Expected an explicit semantic-version release tag")
    path = "web/data/metadata.json" if kind == "atlas" else "research/supplementary/package_manifest.json"
    metadata = json.loads((root / path).read_text())
    if tag != prefix + metadata["version"]:
        raise ValueError("Requested tag does not match checked-out release metadata")
    return metadata


def build_assets(kind, tag, root, output):
    metadata = validate_tag(kind, tag, root)
    if kind == "supplement":
        run(sys.executable, str(root / "scripts/validate_supplement.py"), "--build-output", str(output))
        return sorted(output.iterdir()), "supplement_checksums.sha256"
    names = sorted(n for n in run("git", "ls-files", "-z").split("\0") if n)
    released = date.fromisoformat(metadata["released"])
    archive = output / f"torino-urban-epw-atlas-{tag}.zip"
    with ZipFile(archive, "w", ZIP_DEFLATED) as z:
        for name in names:
            path = root / name
            if not path.is_file() or path.is_symlink():
                raise ValueError(f"Unsupported release file: {name}")
            entry = ZipInfo("torino-urban-epw-atlas/" + name,
                            date_time=(released.year, released.month, released.day, 0, 0, 0))
            entry.compress_type = ZIP_DEFLATED
            entry.external_attr = 0o100644 << 16
            z.writestr(entry, path.read_bytes())
    checksums = output / "SHA256SUMS.txt"
    checksums.write_text(f"{digest(archive)}  {archive.name}\n")
    return [archive, checksums], checksums.name


def zip_contents(path):
    with ZipFile(path) as z:
        names = z.namelist()
        if len(names) != len(set(names)) or z.testzip() is not None:
            raise ValueError(f"Invalid or duplicated archive members: {path.name}")
        return {name: hashlib.sha256(z.read(name)).hexdigest() for name in names}


def verify_assets(expected, downloaded, checksum_name):
    lines = (downloaded / checksum_name).read_text().splitlines()
    checksums = {}
    for line in lines:
        value, name = line.split(maxsplit=1)
        name = name.removeprefix("*")
        if name in checksums or not re.fullmatch(r"[a-f0-9]{64}", value):
            raise ValueError("Invalid or duplicated checksum entry")
        checksums[name] = value
    for source in expected:
        target = downloaded / source.name
        if not target.is_file():
            raise ValueError(f"Missing release asset: {source.name}")
        if source.name == checksum_name:
            continue
        if checksums.get(source.name) != digest(target):
            raise ValueError(f"Release checksum mismatch: {source.name}")
        if source.suffix == ".zip":
            # Compression libraries can differ; verify every archived byte instead.
            if zip_contents(source) != zip_contents(target):
                raise ValueError(f"Release archive differs from tagged source: {source.name}")
        elif digest(source) != digest(target):
            raise ValueError(f"Release asset differs from tagged source: {source.name}")


def publish_or_verify(kind, tag, repository, root, assets, checksum_name):
    pages = json.loads(run("gh", "api", f"repos/{repository}/releases", "--paginate", "--slurp"))
    existing = [r for page in pages for r in page if r["tag_name"] == tag]
    if len(existing) > 1:
        raise ValueError("Multiple releases have the requested tag")
    if existing:
        release = existing[0]
        if release["draft"]:
            raise ValueError("An unpublished draft exists; review it explicitly before publication")
        required = {p.name for p in assets}
        if not required <= {a["name"] for a in release["assets"]}:
            raise ValueError("Existing release is incomplete; no assets were overwritten")
        with tempfile.TemporaryDirectory(prefix="release-download-") as tmp:
            args = ["gh", "release", "download", tag, "--repo", repository, "--dir", tmp]
            for name in sorted(required):
                args.extend(["--pattern", name])
            run(*args)
            verify_assets(assets, Path(tmp), checksum_name)
        print(f"PASS: {tag} already published; all required downloads match the tagged source. No changes made.")
        return "verified"
    title = (f"Torino Urban EPW Atlas {tag}" if kind == "atlas" else
             f"Torino study supplementary material {tag.removeprefix('supplement-')}")
    run("gh", "release", "create", tag, "--repo", repository, "--verify-tag",
        "--latest" if kind == "atlas" else "--latest=false", "--title", title,
        "--notes-file", str(root / f"docs/release-notes-{tag}.md"),
        *(str(p) for p in assets))
    print(f"Published {tag}.")
    return "created"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kind", choices=["atlas", "supplement"], required=True)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--repository", required=True)
    args = parser.parse_args()
    root = Path.cwd()
    validate_tag(args.kind, args.tag, root)
    remote_commit = json.loads(run("gh", "api", f"repos/{args.repository}/commits/{args.tag}"))["sha"]
    if remote_commit != run("git", "rev-parse", "HEAD"):
        raise ValueError("Check out the exact published tag before running this helper")
    if run("git", "status", "--porcelain", "--untracked-files=no"):
        raise ValueError("Tracked release files have local changes")
    with tempfile.TemporaryDirectory(prefix="release-build-") as tmp:
        assets, checksums = build_assets(args.kind, args.tag, root, Path(tmp))
        publish_or_verify(args.kind, args.tag, args.repository, root, assets, checksums)


if __name__ == "__main__":
    main()
