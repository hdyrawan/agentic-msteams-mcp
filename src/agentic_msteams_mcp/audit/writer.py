import hashlib
import json
import os
import logging
from datetime import datetime, timezone
from typing import Any, Dict
from ..notifications.models import NotificationRequest, NotificationResult
from ..asks.models import UserAsk, AskState
from ..config import settings

logger = logging.getLogger("msteams-audit")

def generate_stable_fingerprint(obj: Any) -> str:
    '''Generate a stable SHA-256 fingerprint of an object (excludes bodies).'''
    if hasattr(obj, "model_dump"): # Pydantic model
        data = obj.model_dump()
        # Convert datetimes to ISO strings for JSON serialization
        for k, v in data.items():
            if isinstance(v, datetime):
                data[k] = v.isoformat()
        # Filter out body fields to avoid sensitive logging
        for field in ["message", "question", "reply_text", "description", "reason", "text"]:
            data.pop(field, None)
        canonical_json = json.dumps(data, sort_keys=True)
    elif isinstance(obj, dict):
        # If it's already a filtered dict
        canonical_json = json.dumps(obj, sort_keys=True)
    else:
        canonical_json = json.dumps({"raw": str(obj)}, sort_keys=True)
        
    return hashlib.sha256(canonical_json.encode()).hexdigest()

def write_audit_log(request: Any, result: Any, event_type: str = "notification") -> str:
    '''Write an append-only audit log of a request/result pair.'''
    fingerprint = generate_stable_fingerprint(request)
    
    # Normalize results to extract status/reason accurately for both objects and dicts
    if isinstance(result, dict):
        status = result.get("status", "unknown")
        reason = result.get("reason", "")
    else:
        status = getattr(result, "status", "unknown")
        reason = getattr(result, "reason", "")
    
    # Extract target ID from request (works for Pydantic models or dicts)
    target_id = "UNKNOWN"
    if isinstance(request, dict):
        target_id = request.get("target_user_id") or request.get("approval_id") or request.get("reply_to", "UNKNOWN")
    else:
        target_id = getattr(request, "target_id", getattr(request, "target_user_id", "UNKNOWN"))

    audit_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": event_type,
        "target_id": target_id,
        "decision": "ALLOWED" if (hasattr(result, "delivered") and result.delivered) or status == "success" else "DENIED",
        "reason": reason,
        "fingerprint": fingerprint,
        "status": status
    }

    log_line = json.dumps(audit_entry)
    log_dir = os.path.dirname(settings.msteams_audit_log_path)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    with open(settings.msteams_audit_log_path, "a", encoding="utf-8") as f:
        f.write(log_line + "\n")

    return f"audit-{int(datetime.now().timestamp())}-{fingerprint[:8]}"
