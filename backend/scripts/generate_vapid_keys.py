"""Generate a VAPID keypair for Web Push.

Run once per environment, paste output into .env, restart backend:

    docker compose exec backend python scripts/generate_vapid_keys.py

Both keys must be persisted: rotating either one invalidates every push
subscription saved in push_subscriptions. Treat VAPID_PRIVATE_KEY as a
secret (never commit, never log).

The public key is printed in the base64url uncompressed-EC-point format
that the browser's pushManager.subscribe expects as `applicationServerKey`.
"""

from __future__ import annotations

import base64

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def main() -> None:
    private_key = ec.generate_private_key(ec.SECP256R1())

    # pywebpush's Vapid.from_string strips newlines then base64url-decodes,
    # so it expects the DER body of the PKCS#8 PEM, base64url-encoded —
    # NOT the PEM with headers. This format is also single-line which
    # pastes cleanly into .env.
    private_der = private_key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    private_b64url = _b64url(private_der)

    # Browsers want the raw 65-byte uncompressed point (0x04 || X || Y),
    # base64url-encoded. This is what pushManager.subscribe consumes as
    # applicationServerKey.
    public_raw = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint,
    )
    public_b64url = _b64url(public_raw)

    print("# Paste these two lines into .env (overwrite existing VAPID_* values):")
    print()
    print(f"VAPID_PRIVATE_KEY={private_b64url}")
    print(f"VAPID_PUBLIC_KEY={public_b64url}")
    print()
    print("# Then restart the backend: docker compose restart backend")


if __name__ == "__main__":
    main()
