from typing import Dict, Optional
from .models import UserAsk

class AskStore:
    """In-memory store for pending user asks (v0.3.0). 
    Note: Restarts clear all pending asks."""
    def __init__(self):
        self._asks: Dict[str, UserAsk] = {}

    async def save(self, ask: UserAsk) -> None:
        self._asks[ask.request_id] = ask

    async def get(self, request_id: str) -> Optional[UserAsk]:
        return self._asks.get(request_id)

    async def update_state(self, request_id: str, state: str, reply: Optional[str] = None) -> Optional[UserAsk]:
        ask = await self.get(request_id)
        if ask:
            ask.state = state
            if reply:
                ask.reply_text = reply
            return ask
        return None

store = AskStore()
