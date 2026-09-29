"""Run from any working directory; dependencies are loaded from this repository."""
import logging
import site
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VENDOR = ROOT / "vendor"
sys.path.insert(0, str(VENDOR))
sys.path.insert(0, str(ROOT))
# The official Windows SDK dependency pywin32 uses a .pth bootstrap for DLLs.
# Only the trusted, locally built dependency directory is processed.
site.addsitedir(str(VENDOR))
logging.basicConfig(stream=sys.stderr, level=logging.WARNING, format="%(levelname)s %(name)s %(message)s")


if __name__ == "__main__":
    try:
        from offerproof.config import APP_VERSION
        from offerproof.server import main
        print(f"OfferProof {APP_VERSION}: disclosure previews and presentation timing diagnostics enabled; waiting for MCP requests.", file=sys.stderr)
        main()
    except ImportError:
        print("OfferProof dependencies unavailable. Build vendor on a compatible Python 3.13 x64 machine; see vendor/README.md.", file=sys.stderr)
        raise SystemExit(2)
    except Exception:
        print("OfferProof startup failed safely. Validate synthetic configuration and repository runtime permissions.", file=sys.stderr)
        raise SystemExit(3)
