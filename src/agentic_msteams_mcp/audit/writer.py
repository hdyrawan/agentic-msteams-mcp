import hashlib
import json
import os
import logging
from datetime import datetime, timezone
from typing import Any, Dict
from ..notifications.models import NotificationRequest, NotificationResult
from ..config import settings

logger = logging.getLogger("msteams-audit")

def generate_stable_fingerprint(request: NotificationRequest) -> str:
    '''
    Generate a stable SHA-256 fingerprint of the request.
    Intentionally excludes the message body to avoid sensitive data in logs.
    '''
    # We use getattr for safety since placeholder objects might be used during validation fails
    payload = {
        "target_type": getattr(request, "target_type", "UNKNOWN"),
        "target_id": getattr(request, "target_id", "UNKNOWN"),
        "title": getattr(request, "title", "UNKNOWN"),
        "severity": getattr(request, "severity", "UNKNOWN"),
        "correlation_id": getattr(request, "correlation_id", None),
        "metadata": getattr(request, "metadata", None)
    }
    canonical_json = json.dumps(payload, sort_keys=True)
    return hashlib.sha256(canonical_json.encode()).hexdigest()

def write_audit_log(request: NotificationRequest, result: NotificationResult) -> str:
    '''
    Write an append-only local audit log of the notification attempt to configurable path.
    Returns a unique audit_id.
    '''
    fingerprint = generate_stable_fingerprint(request)
    
    audit_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tool": "msteams_send_notification",
        "target_type": getattr(request, "target_type", "UNKNOWN"),
        "target_id": getattr(request, "target_id", "UNKNOWN"),
        "severity": getattr(request, "severity", "UNKNOWN"),
        "decision": "ALLOWED" if result.delivered else "DENIED",
        "reason": result.reason,
        "correlation_id": getattr(request, "correlation_id", None),
        "fingerprint": fingerprint,
        "status": result.status
    }

    log_line = json.dumps(audit_entry)
    
    log_dir = os.path.dirname(settings.msteams_audit_log_path)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    with open(settings.msteams_audit_log_path, "a", encoding="utf-8") as f:
        f.write(log_line + "\n")

    return f"audit-{int(datetime.now().timestamp())}-{fingerprint[:8]}"
