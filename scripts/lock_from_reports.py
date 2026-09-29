"""Freeze exactly the verified artifacts in pip's installation reports."""
import argparse
import json
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("reports", nargs="+", type=Path)
parser.add_argument("--output", type=Path, default=Path("requirements.lock"))
args = parser.parse_args()
packages = {}
for report_path in args.reports:
    report = json.loads(report_path.read_text(encoding="utf-8"))
    for item in report["install"]:
        metadata = item["metadata"]
        key = metadata["name"].lower().replace("_", "-")
        version, hashes = packages.setdefault(key, (metadata["version"], set()))
        if version != metadata["version"]:
            raise SystemExit("Conflicting package versions; resolve and verify before locking.")
        hashes.add(item["download_info"]["archive_info"]["hashes"]["sha256"])
lines = ["# Verified official MCP 2.2.0 dependency artifacts for Windows x64 Python 3.13.",
         "# Includes development cp312 wheel hashes where different; target build still enforces 3.13."]
for name, (version, hashes) in sorted(packages.items()):
    lines.append(name + "==" + version + "".join(" --hash=sha256:" + h for h in sorted(hashes)))
args.output.write_text("\n".join(lines) + "\n", encoding="utf-8")
