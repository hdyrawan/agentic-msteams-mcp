import logging
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict
from ..notifications.models import NotificationRequest, NotificationResult
from ..config import settings

logger = logging.getLogger("msteams-audit")

def write_audit_log(request: NotificationRequest, result: NotificationResult) -> str:
    '''
    Write an append-only local audit log of the notification attempt to configurable path.
    Returns a unique audit_id.
    '''
    fingerprint = hash(f"{request.target_id}:{request.title}")
    
    audit_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tool": "msteams_send_notification",
        "target_type": request.target_type,
        "target_id": request.target_id,
        "severity": request.severity,
        "decision": "ALLOWED" if result.delivered else "DENIED",
        "reason": result.reason,
        "correlation_id": request.correlation_id,
        "fingerprint": fingerprint,
        "status": result.status
    }

    log_line = json.dumps(audit_entry)
    
    # Ensure data directory exists
    log_dir = os.path.dirname(settings.msteams_audit_log_path)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    with open(settings.msteams_audit_log_path, "a", encoding="utf-8") as f:
        f.write(log_line + "\n")

    return f"audit-{int(datetime.now().timestamp())}-{fingerprint}"
