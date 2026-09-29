import json
import os
import subprocess
import sys
import unittest
from importlib.util import find_spec
from pathlib import Path
from offerproof.config import ROOT


@unittest.skipUnless(find_spec("mcp") is not None, "MCP SDK needed for subprocess transport test")
class StdioTests(unittest.TestCase):
    def test_31_stdout_contains_only_jsonrpc(self):
        # Use an SDK bootstrap for the development-runtime test. The target
        # runtime uses run_mcp.py directly with its actual cp313 vendor tree.
        import mcp
        sdk = str(Path(mcp.__file__).resolve().parent.parent)
        boot = "import site,sys,runpy; sys.path.insert(0," + repr(sdk) + "); site.addsitedir(" + repr(sdk) + "); import mcp; runpy.run_path(" + repr(str(ROOT / "run_mcp.py")) + ",run_name='__main__')"
        process = subprocess.Popen([sys.executable, "-c", boot], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True, encoding="utf-8", cwd=ROOT.parent,
            env={**os.environ, "PYTHONIOENCODING": "utf-8", "OTEL_SDK_DISABLED": "true"})
        # A legacy client is supported by official 2.x and is a useful explicit
        # wire-format probe. Business workflow is independent of protocol era.
        request = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
            "protocolVersion": "2025-11-25", "capabilities": {}, "clientInfo": {"name": "offerproof-wire-test", "version": "1"}}}
        out, err = process.communicate(json.dumps(request) + "\n", timeout=20)
        self.assertEqual(process.returncode, 0, err)
        self.assertTrue(out.strip(), err)
        messages = [json.loads(line) for line in out.splitlines()]
        self.assertTrue(all(message.get("jsonrpc") == "2.0" for message in messages))
        self.assertTrue(any(message.get("id") == 1 and "result" in message for message in messages))
