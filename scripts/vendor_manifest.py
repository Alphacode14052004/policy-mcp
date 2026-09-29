"""Record and verify offline artifact integrity; never signs a release."""
import argparse
import hashlib
import importlib.metadata
import json
import platform
from pathlib import Path


def files(directory):
    return {str(p.relative_to(directory)).replace("\\", "/"): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(directory.rglob("*")) if p.is_file() and "__pycache__" not in p.parts
            and p.name not in ("manifest.json", "README.md") and p.suffix != ".pyc"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", type=Path)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    manifest = args.directory / "manifest.json"
    if args.verify:
        expected = json.loads(manifest.read_text(encoding="utf-8"))
        if expected["files_sha256"] != files(args.directory):
            raise SystemExit("Vendor manifest mismatch: rebuild or restore the verified package.")
        print("Vendor file hashes verified.")
    else:
        packages = sorted(({"name": d.metadata["Name"], "version": d.version} for d in importlib.metadata.distributions(path=[str(args.directory)])), key=lambda p: p["name"].lower())
        result = {"target_python": "3.13", "target_platform": "win_amd64", "manifest_writer_python": platform.python_version(),
                  "packages": packages, "files_sha256": files(args.directory)}
        manifest.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(f"Recorded {len(packages)} package versions and {len(result['files_sha256'])} file hashes.")
