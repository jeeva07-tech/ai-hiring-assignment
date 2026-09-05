import base64
import hashlib
import hmac
import time


WEBHOOK_TIMESTAMP_TOLERANCE_SECONDS = 300


def compute_hunar_signature(
    *,
    api_key: str,
    request_body: bytes,
    timestamp: str,
) -> str:
    message = f"{timestamp.strip()}.".encode("utf-8") + request_body

    digest = hmac.new(
        api_key.encode("utf-8"),
        message,
        hashlib.sha256,
    ).digest()

    return base64.b64encode(digest).decode("ascii")


def verify_hunar_webhook_signature(
    *,
    signature_header: str | None,
    timestamp_header: str | None,
    request_body: bytes,
    trusted_api_keys: list[str],
) -> bool:

    if not signature_header or not signature_header.strip():
        return False

    if not timestamp_header or not timestamp_header.strip():
        return False

    timestamp = timestamp_header.strip()

    # Prevent replay attacks.
    try:
        timestamp_value = int(timestamp)
    except ValueError:
        return False

    current_time = int(time.time())

    if abs(current_time - timestamp_value) > WEBHOOK_TIMESTAMP_TOLERANCE_SECONDS:
        return False

    signatures = [
        signature.strip()
        for signature in signature_header.split(",")
        if signature.strip()
    ]

    for api_key in trusted_api_keys:
        computed = compute_hunar_signature(
            api_key=api_key,
            request_body=request_body,
            timestamp=timestamp,
        )

        for signature in signatures:
            if hmac.compare_digest(signature, computed):
                return True

    return False