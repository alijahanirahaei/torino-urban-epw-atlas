"""Check the public supplement and optionally build its versioned downloads."""

import argparse
import csv
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import shutil
from datetime import date
import xml.etree.ElementTree as ET
from zipfile import ZipFile, ZIP_DEFLATED, ZipInfo

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "research/supplementary"
NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def safe_path(name):
    p = PurePosixPath(name)
    return bool(name) and not p.is_absolute() and ".." not in p.parts and "\\" not in name and ":" not in name


def package_metadata(package):
    metadata = json.loads((package / "package_manifest.json").read_text())
    if not re.fullmatch(r"\d+\.\d+\.\d+", metadata["version"]):
        raise ValueError("Invalid supplementary version")
    date.fromisoformat(metadata["prepared_date"])
    citation = (package / "CITATION.cff").read_text()
    if f"version: {metadata['version']}\n" not in citation:
        raise ValueError("Supplementary version differs from citation metadata")
    return metadata


def validate(package=PACKAGE):
    metadata = package_metadata(package)
    files = {}
    for p in package.rglob("*"):
        if p.is_symlink():
            raise ValueError(f"Symlink in supplement: {p.name}")
        if p.is_file():
            name = p.relative_to(package).as_posix()
            if not safe_path(name) or any(x.startswith(".") or x == "__pycache__" for x in p.relative_to(package).parts):
                raise ValueError(f"Unexpected package path: {name}")
            if p.suffix in {".epw", ".log", ".pyc", ".zip"}:
                raise ValueError(f"Unexpected package file: {name}")
            files[name] = p
    expected = {}
    for line in (package / "CHECKSUMS.sha256").read_text().splitlines():
        digest, name = line.split("  ", 1)
        if not safe_path(name) or name in expected:
            raise ValueError("Unsafe or duplicate checksum entry")
        expected[name] = digest
    if set(expected) != set(files) - {"CHECKSUMS.sha256"}:
        raise ValueError("Checksum manifest does not cover exactly the packaged files")
    for name, digest in expected.items():
        if sha(files[name]) != digest:
            raise ValueError(f"Checksum mismatch: {name}")
    with (package / "FILE_INDEX.csv").open(newline="") as stream:
        index = list(csv.DictReader(stream))
    if {r["path"] for r in index} != set(files) - {"CHECKSUMS.sha256", "FILE_INDEX.csv"} or len(index) != len(files) - 2:
        raise ValueError("File index coverage mismatch")
    for row in index:
        if row["sha256"] != sha(files[row["path"]]) or not row["purpose"]:
            raise ValueError(f"File index mismatch: {row['path']}")
    table_numbers = {int(re.match(r"S(\d+)_", p.name).group(1)) for p in (package / "tables").glob("S*.csv")}
    if table_numbers != set(range(1, 14)):
        raise ValueError("Expected supplementary tables S1-S13")
    for p in package.rglob("*.csv"):
        with p.open(newline="") as stream:
            reader = csv.reader(stream)
            header = next(reader)
            if not header or len(set(header)) != len(header):
                raise ValueError(f"Invalid CSV header: {p.name}")
            for row in reader:
                if len(row) != len(header):
                    raise ValueError(f"Invalid CSV width: {p.name}")
    for p in package.rglob("*.json"):
        json.loads(p.read_text())
    with (package / "heat_sensitivity/run_manifest.csv").open(newline="") as stream:
        jobs = list(csv.DictReader(stream))
    if len(jobs) != 105 or len({r["job_id"] for r in jobs}) != 105:
        raise ValueError("Expected 105 unique heat jobs")
    for job in jobs:
        if not safe_path(job["config_file"]):
            raise ValueError("Unsafe configuration path")
        path = package / "heat_sensitivity" / job["config_file"]
        if sha(path) != job["config_sha256"]:
            raise ValueError(f"Configuration hash mismatch: {job['job_id']}")
        cfg = json.loads(path.read_text())
        if (cfg["nday"], cfg["dtsim"], cfg["dtweather"], cfg["zone"], cfg["flr_h"], cfg["charlength"]) != (365, 300, 3600, "4A", 3.05, 500):
            raise ValueError(f"Unexpected annual setup: {job['job_id']}")
    for row in json.loads((package / "configuration_provenance.json").read_text()):
        if not safe_path(row["json"]) or sha(package / row["json"]) != row["json_sha256"]:
            raise ValueError("Category configuration provenance mismatch")
    texts = []
    for name, path in files.items():
        if path.suffix in {".md", ".txt", ".csv", ".json", ".py", ".cff"}:
            texts.append(path.read_text())
    with ZipFile(package / "supplementary_material.docx") as doc:
        if any("comments" in n.lower() for n in doc.namelist()):
            raise ValueError("Word comments present")
        for name in doc.namelist():
            if name.endswith(".xml"):
                tree = ET.fromstring(doc.read(name))
                texts.append(" ".join(tree.itertext()))
                if any(tree.findall(".//w:" + tag, NS) for tag in ("ins", "del", "moveFrom", "moveTo", "trackRevisions")):
                    raise ValueError("Word revisions or tracking enabled")
        body = ET.fromstring(doc.read("word/document.xml"))
        rels = ET.fromstring(doc.read("word/_rels/document.xml.rels"))
        images = {r.attrib["Id"]: r.attrib["Target"] for r in rels
                  if r.attrib.get("Type", "").endswith("/image")}
        drawing_ns = "http://schemas.openxmlformats.org/drawingml/2006/main"
        relationship_ns = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
        embedded = []
        for blip in body.findall(f".//{{{drawing_ns}}}blip"):
            target = images[blip.attrib[f"{{{relationship_ns}}}embed"]]
            if not safe_path(target):
                raise ValueError("Unsafe document image path")
            embedded.append(hashlib.sha256(doc.read("word/" + target)).hexdigest())
        supplied = {sha(p) for p in (package / "figures").glob("*.png")}
        if len(embedded) != 6 or set(embedded) != supplied:
            raise ValueError("Embedded figures differ from the six supplied PNGs")
        paragraphs = ["".join(p.itertext()) for p in body.findall("w:body/w:p", NS)]
        for n in range(1, 8):
            if not any(p.startswith(f"S{n} ") for p in paragraphs):
                raise ValueError(f"Missing section S{n}")
        if len(body.findall(".//w:tbl", NS)) != 5:
            raise ValueError("Embedded table count differs from five")
        for n in range(1, 14):
            if f"Supplementary Table S{n}" not in paragraphs:
                raise ValueError(f"Missing table caption S{n}")
        for n in range(1, 7):
            if f"Supplementary Figure S{n}" not in paragraphs:
                raise ValueError(f"Missing figure caption S{n}")
    if not (package / "supplementary_material.pdf").read_bytes().startswith(b"%PDF-"):
        raise ValueError("Missing PDF reading copy")
    joined = "\n".join(texts)
    patterns = [r"/(?:Users|home)/[^/\s]+/", r"[A-Za-z]:\\Users\\", r"Rev01/", r"revision_workspace_",
                r"\b(?:ChatGPT|Codex|OpenAI)\b", r"\bas an AI\b", r"\bTODO\b", r"ghp_[A-Za-z0-9]{20,}",
                r"github_pat_[A-Za-z0-9_]{20,}", r"BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY"]
    for pattern in patterns:
        if re.search(pattern, joined, re.I):
            raise ValueError("Private path, editorial placeholder, or unintended tool text in public supplement")
    return {"status": "PASS", "version": metadata["version"], "files": len(files), "table_csvs": 13, "heat_configurations": 105,
            "embedded_tables": 5, "sections": 7, "figures": 6}


def build(output, package=PACKAGE):
    validate(package)
    output = output.resolve()
    if output == ROOT or ROOT in output.parents:
        raise ValueError("Release artifacts must be built outside the repository")
    output.mkdir(parents=True, exist_ok=True)
    metadata = package_metadata(package)
    prepared = date.fromisoformat(metadata["prepared_date"])
    archive = output / f"torino_uwg_supplement_v{metadata['version']}.zip"
    with ZipFile(archive, "w", ZIP_DEFLATED) as z:
        for p in sorted(package.rglob("*")):
            if p.is_file():
                entry = ZipInfo(p.relative_to(package).as_posix(), date_time=(prepared.year, prepared.month, prepared.day, 0, 0, 0))
                entry.compress_type = ZIP_DEFLATED
                entry.external_attr = 0o100644 << 16
                z.writestr(entry, p.read_bytes())
    assets = [archive]
    for name in ("supplementary_material.docx", "supplementary_material.pdf"):
        target = output / name
        shutil.copyfile(package / name, target)
        assets.append(target)
    (output / "supplement_checksums.sha256").write_text("".join(f"{sha(p)}  {p.name}\n" for p in assets))
    return assets


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-output", type=Path)
    args = parser.parse_args()
    print(json.dumps(validate(), indent=2))
    if args.build_output:
        for asset in build(args.build_output):
            print(asset)
