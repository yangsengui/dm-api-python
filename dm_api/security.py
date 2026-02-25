"""Signature verification helpers."""

import base64
import json
from typing import Any, Callable, Dict

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding


class SignatureVerifier:
    def __init__(self, public_key_pem: str) -> None:
        self._public_key = serialization.load_pem_public_key(public_key_pem.encode("utf-8"))

    def check_signature(
        self,
        data: Dict[str, Any],
        nonce: str,
        canonicalizer: Callable[[str], str],
    ) -> bool:
        signature = data.get("signature")
        if not signature:
            return False

        try:
            sig = base64.b64decode(signature)
            payload = {k: v for k, v in data.items() if k != "signature"}
            payload["nonce_str"] = nonce

            json_str = json.dumps(payload, separators=(",", ":"))
            canonical = canonicalizer(json_str)
            if not canonical:
                return False

            self._public_key.verify(
                sig,
                canonical.encode("utf-8"),
                padding.PKCS1v15(),
                hashes.SHA256(),
            )
            return True
        except Exception:
            return False
