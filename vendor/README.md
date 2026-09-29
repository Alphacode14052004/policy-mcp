# Offline dependency bundle

This directory contains the locally built **Windows x64 CPython 3.13** dependencies, including official `mcp==2.2.0`. Binary dependencies are architecture/Python specific. Do not use this bundle with Python 3.12 or ARM64.

Package files and runtime artifacts are deliberately ignored by source control. `requirements.lock` pins exact package versions and verified wheel hashes. `manifest.json` records the built files' SHA-256 hashes and package versions. This is integrity evidence, not a signed release or a vulnerability scan.

On a compatible full Windows Python 3.13 x64 build machine with approved package access:

```powershell
./scripts/build_vendor.ps1
```

The script validates the interpreter and lock, creates an isolated build environment under `.build/` outside `vendor/`, installs only compatible hashed wheels into staging, then clears only this repository's verified vendor children and copies the packages. An incompatible wheel or failed download leaves the old vendor intact. It never copies a virtual environment. Build temporary files remain under `.build/` for inspection.

Transfer the source, JSON fixtures and populated `vendor/` directory together. Exclude `.build/`, runtime keys/databases/logs, prompt-history files and test artifacts unless needed. On the target:

```powershell
./scripts/verify_offline.ps1
./scripts/smoke_test.ps1
py -3.13 run_mcp.py
```

No pip or internet is needed on the target. `verify_offline.ps1` validates hashes, imports the SDK from vendor, denies socket connections during the startup/smoke probe and runs tests. It does not disable the operating system network interface. `run_mcp.py` processes trusted vendor `.pth` files so the official Windows `pywin32` dependency can locate its modules/DLLs.

This workspace initially lacked a registered Python runtime. Verification used an isolated official embeddable CPython 3.13.7 runtime under `.build/python313/` and CPython 3.13 wheels fetched with pip's explicit target flags from the available build interpreter. The embeddable runtime is a local verification tool, not a portable virtual environment and not included in the source deliverable. The standard `build_vendor.ps1` venv path requires a full Python installation with ensurepip; its verification status is recorded in docs/SDK_VERIFICATION.md.

Updating dependencies is deliberate: resolve into an isolated directory, inspect official SDK API changes, run contract tests, create pip reports, then regenerate the lock with `scripts/lock_from_reports.py` and rebuild. Never remove TLS verification or add trusted-host exceptions.
