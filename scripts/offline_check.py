import json
import site
import socket
import sys
import tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "vendor")]
site.addsitedir(str(ROOT / "vendor"))


def deny_network(*args, **kwargs):
    raise RuntimeError("Network forbidden during offline verification")


socket.create_connection = deny_network
socket.getaddrinfo = deny_network
socket.socket.connect = deny_network
socket.socket.connect_ex = deny_network
from offerproof.server import OfferProofServer
from offerproof.core.orchestration import OfferProof
from scripts.demo import run

with tempfile.TemporaryDirectory(prefix="offerproof-offline-") as directory:
    service = OfferProof(runtime=Path(directory))
    server = OfferProofServer(service)
    assert run(service)["success"]
    with service.store.connect() as connection:
        assert service.audit.verify_chain(connection)
print(json.dumps({"offline_import": True, "sqlite_startup": True, "smoke": True, "network_calls_allowed": False}))
