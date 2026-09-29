import argparse
import json
import platform
import site
import sys
import time
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


class RecordedResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.records = []

    def addSuccess(self, test):
        super().addSuccess(test)
        self.records.append({"test": test.id(), "status": "PASS"})

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.records.append({"test": test.id(), "status": "FAIL"})

    def addError(self, test, err):
        super().addError(test, err)
        self.records.append({"test": test.id(), "status": "ERROR"})

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self.records.append({"test": test.id(), "status": "SKIP", "reason": reason})


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--sdk-dir", type=Path, default=ROOT / "vendor")
    parser.add_argument("--output", type=Path, default=ROOT / "eval/results/tests.json")
    parser.add_argument("--core-only", action="store_true")
    args = parser.parse_args()
    if not args.core_only:
        sys.path.insert(0, str(args.sdk_dir.resolve()))
        site.addsitedir(str(args.sdk_dir.resolve()))
        import mcp
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"), top_level_dir=str(ROOT))
    started = time.perf_counter()
    result = unittest.TextTestRunner(verbosity=2, resultclass=RecordedResult).run(suite)
    report = {"python": platform.python_version(), "platform": platform.platform(), "duration_seconds": time.perf_counter() - started,
              "tests_run": result.testsRun, "failures": len(result.failures), "errors": len(result.errors), "skipped": len(result.skipped),
              "success": result.wasSuccessful(), "tests": result.records}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    raise SystemExit(0 if result.wasSuccessful() else 1)
