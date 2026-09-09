#!/usr/bin/env python3
"""Reproduce packaged UWG heat cases from exact JSONs and separately obtained forcing."""

from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor, wait, FIRST_COMPLETED
import contextlib
import csv
import hashlib
import json
import multiprocessing
import os
from pathlib import Path
import sys
import time
import traceback

PACKAGE = Path(__file__).resolve().parent
RAW_SHA = "3430967c3faa30aa3512a34c8fb636003458f162b50c2d2b5ded70707f76a71a"
EFFECTIVE_SHA = "39c5c8cb90b39fefdfb531ade96700e9436d4df9c8fca3a57191f820d135e5a9"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(value, indent=2) + "\n")
    os.replace(tmp, path)


def source_copy(source, output):
    source_hash = sha(source)
    if source_hash == EFFECTIVE_SHA:
        return source.resolve()
    if source_hash != RAW_SHA:
        raise ValueError(
            "Forcing does not match the documented raw or pressure-prepared AvMY Caselle file."
        )
    lines = source.read_text().splitlines()
    if len(lines) != 8768:
        raise ValueError("Expected eight headers and 8760 hours.")
    rows = [line.split(",") for line in lines[8:]]
    for row in rows:
        if len(row) != 35:
            raise ValueError("Unexpected raw EPW schema.")
        row[9] = f"{float(row[9]) * 100:.0f}"
    prepared = output / "forcing_pressure_pa.epw"
    prepared.write_text("\n".join(lines[:8] + [",".join(r) for r in rows]) + "\n")
    if sha(prepared) != EFFECTIVE_SHA:
        raise ValueError("Prepared forcing hash mismatch.")
    return prepared.resolve()


def normalize(path):
    lines = path.read_text().splitlines()
    if len(lines) != 8768:
        raise ValueError("Output is not annual.")
    result = []
    for line in lines[8:]:
        row = line.split(",")
        if len(row) == 36 and row[-1] == row[-2]:
            row = row[:-1]
        if len(row) != 35:
            raise ValueError("Unexpected output schema; not repairing unknown fields.")
        result.append(",".join(row))
    path.write_text("\n".join(lines[:8] + result) + "\n")


def worker(job):
    from uwg import UWG

    started = time.monotonic()
    config = json.loads(Path(job["config_path"]).read_text())
    output = Path(job["output"])
    log = output / "logs" / f"{job['job_id']}.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    p3 = output / "precision3" / f"{job['job_id']}.epw"
    p1 = output / "precision1" / f"{job['job_id']}.epw"
    for p in [p3, p1]:
        p.parent.mkdir(parents=True, exist_ok=True)
    result = {
        "job_id": job["job_id"],
        "config_sha256": sha(job["config_path"]),
        "effective_forcing_sha256": sha(job["forcing"]),
    }
    try:
        with log.open("w") as handle, contextlib.redirect_stdout(
            handle
        ), contextlib.redirect_stderr(handle):
            model = UWG.from_dict(
                config,
                epw_path=job["forcing"],
                new_epw_dir=str(p3.parent),
                new_epw_name=p3.name,
            )
            model.generate()
            model.simulate()
            for precision, path in [(3, p3), (1, p1)]:
                temporary = path.with_suffix(".partial.epw")
                model.epw_precision = precision
                model._new_epw_dir = str(temporary.parent)
                model._new_epw_name = temporary.name
                model._new_epw_path = None
                model.write_epw()
                normalize(temporary)
                os.replace(temporary, path)
                result[f"epw{precision}_path"] = str(path)
                result[f"epw{precision}_sha256"] = sha(path)
                result[f"matches_archived_epw{precision}"] = (
                    sha(path) == job[f"expected_epw{precision}_sha256"]
                )
        result["status"] = "success"
    except Exception as exc:
        result.update(status="failed", error=repr(exc))
        with log.open("a") as handle:
            traceback.print_exc(file=handle)
    result["seconds"] = round(time.monotonic() - started, 3)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--forcing", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--workers", type=int, choices=range(1, 5), default=4)
    parser.add_argument(
        "--jobs",
        help="Comma-separated exact job IDs C0-C6; omit for all seven medoids. Released library: C1,C2,C4,C6",
    )
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    import uwg

    if uwg.__version__ != "5.3.4":
        raise RuntimeError("This runner's serialization adapter requires UWG 5.3.4.")
    with (PACKAGE / "run_manifest.csv").open(newline="") as handle:
        jobs = list(csv.DictReader(handle))
    wanted = set(args.jobs.split(",")) if args.jobs else {j["job_id"] for j in jobs}
    if not wanted <= {j["job_id"] for j in jobs}:
        raise ValueError("Unknown job ID.")
    jobs = [j for j in jobs if j["job_id"] in wanted]
    for j in jobs:
        path = (PACKAGE / j["config_file"]).resolve()
        if PACKAGE.resolve() not in path.parents or sha(path) != j["config_sha256"]:
            raise ValueError(f"Configuration path/hash mismatch: {j['job_id']}")
        config = json.loads(path.read_text())
        if (config["nday"], config["dtsim"], config["dtweather"]) != (365, 300, 3600):
            raise ValueError("Expected frozen annual configuration.")
        j["config_path"] = str(path)
    if sha(args.forcing) not in {RAW_SHA, EFFECTIVE_SHA}:
        raise ValueError("Forcing hash mismatch.")
    if args.check_only:
        print(
            f"Verified {len(jobs)} annual configurations and source forcing; no simulation."
        )
        return
    output = args.output.resolve()
    if output == PACKAGE.resolve() or PACKAGE.resolve() in output.parents:
        raise ValueError(
            "Write simulation outputs outside the immutable supplement package."
        )
    output.mkdir(parents=True, exist_ok=True)
    lock = output / "coordinator.pid"
    if lock.exists():
        try:
            os.kill(int(lock.read_text()), 0)
        except ProcessLookupError:
            lock.unlink()
        else:
            raise RuntimeError(
                "A coordinator may already be running in this output folder."
            )
    with lock.open("x") as handle:
        handle.write(str(os.getpid()))
    began = time.monotonic()
    ledger_path = output / "run_status.json"
    ledger = json.loads(ledger_path.read_text()) if ledger_path.exists() else {}
    try:
        forcing = source_copy(args.forcing, output)
        pending = []
        for job in jobs:
            old = ledger.get(job["job_id"])
            if old and old["status"] == "success":
                if old["config_sha256"] != job["config_sha256"]:
                    raise RuntimeError("Completed configuration mismatch.")
                for p in [1, 3]:
                    if sha(old[f"epw{p}_path"]) != old[f"epw{p}_sha256"]:
                        raise RuntimeError(
                            "Completed EPW changed; refusing to overwrite."
                        )
                continue
            if old:
                archive = (
                    output / "failed_attempts" / f"{job['job_id']}_{time.time_ns()}"
                )
                archive.mkdir(parents=True)
                atomic_json(archive / "status.json", old)
                old_log = output / "logs" / f"{job['job_id']}.log"
                if old_log.exists():
                    old_log.replace(archive / "run.log")
            job.update(forcing=str(forcing), output=str(output))
            pending.append(job)

        def checkpoint(state):
            atomic_json(ledger_path, ledger)
            atomic_json(
                output / "heartbeat.json",
                {
                    "updated_unix_seconds": time.time(),
                    "state": state,
                    "selected": len(jobs),
                    "completed": sum(
                        ledger.get(j["job_id"], {}).get("status") == "success"
                        for j in jobs
                    ),
                    "elapsed_seconds": round(time.monotonic() - began, 1),
                    "python": sys.version,
                    "uwg": uwg.__version__,
                },
            )

        checkpoint("running")
        with ProcessPoolExecutor(
            args.workers, mp_context=multiprocessing.get_context("spawn")
        ) as pool:
            active = {pool.submit(worker, j): j for j in pending}
            while active:
                done, _ = wait(active, timeout=30, return_when=FIRST_COMPLETED)
                for future in done:
                    job = active.pop(future)
                    result = future.result()
                    ledger[job["job_id"]] = result
                    print(job["job_id"], result["status"], flush=True)
                checkpoint("running")
        failed = [
            j["job_id"] for j in jobs if ledger[j["job_id"]]["status"] != "success"
        ]
        checkpoint("complete" if not failed else "complete_with_failures")
        if failed:
            raise RuntimeError(f"Failed cases retained in ledger: {failed}")
        mismatches = [
            j["job_id"]
            for j in jobs
            if not all(ledger[j["job_id"]][f"matches_archived_epw{p}"] for p in [1, 3])
        ]
        print(
            f"Completed {len(jobs)} cases; archived byte-hash mismatches: {mismatches}"
        )
        if mismatches:
            raise RuntimeError(
                "Outputs differ from archived hashes; inspect before claiming exact reproduction."
            )
    finally:
        lock.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
