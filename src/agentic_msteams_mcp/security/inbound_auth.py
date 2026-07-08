import hmac
from typing import Tuple, Optional
from ..config import settings

def validate_inbound_secret(provided_secret: Optional[str]) -> Tuple[bool, str]:
    """
    Validates the inbound shared secret for Microsoft Teams callback requests.
    Returns a tuple of (is_valid, message).
    """
    if not settings.msteams_require_inbound_auth:
        return True, "Auth not required"

    configured_secret = settings.msteams_inbound_shared_secret
    
    if not configured_secret:
        return False, "Inbound auth not configured"

    if provided_secret is None:
        return False, "Missing inbound secret"

    # Use hmac.compare_digest to prevent timing attacks
    if hmac.compare_digest(configured_secret, provided_secret):
        return True, "OK"
    
    return False, "Invalid inbound secret"
