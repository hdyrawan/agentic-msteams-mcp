from abc import ABC, abstractmethod
import uuid
from typing import Optional
from .models import NotificationRequest, NotificationResult

class NotificationSender(ABC):
    '''Interface for Teams notification delivery.'''
    
    @abstractmethod
    async def send(self, request: NotificationRequest) -> NotificationResult:
        pass

class DryRunNotificationSender(NotificationSender):
    '''Safe placeholder sender for v0.2.0 development.'''
    
    async def send(self, request: NotificationRequest) -> NotificationResult:
        return NotificationResult(
            status="success",
            notification_id=str(uuid.uuid4()),
            target_type=request.target_type,
            target_id=request.target_id,
            delivered=True,
            dry_run=True,
            reason="Dry-run delivery successful"
        )
