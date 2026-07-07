from ..config import settings
from ..notifications.models import TargetType

def is_target_allowed(target_type: TargetType, target_id: str) -> bool:
    '''Check if the notification target is in the allowlist loaded from config.'''
    if target_type == TargetType.USER:
        return target_id in settings.msteams_allowed_user_ids
    elif target_type == TargetType.CHANNEL:
        return target_id in settings.msteams_allowed_channel_ids
    return False
