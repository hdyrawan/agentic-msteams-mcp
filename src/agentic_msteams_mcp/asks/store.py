import json
import os
import tempfile
from typing import Dict, Optional
from pathlib import Path
from .models import UserAsk
from ..config import settings

class AskStore:
    """Store for pending user asks (v0.5.0b).
    Supports optional durable JSON persistence via configuration.
    """
    def __init__(self):
        self._asks: Dict[str, UserAsk] = {}
        if settings.msteams_use_durable_state:
            self._load()

    def _load(self) -> None:
        """Load asks from the persistent state file if it exists."""
        path = Path(settings.msteams_state_store_path)
        if not path.exists():
            return

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            asks_data = data.get("asks", {})
            for rid, ask_dict in asks_data.items():
                self._asks[rid] = UserAsk.model_validate(ask_dict)
        except (json.JSONDecodeError, Exception):
            # Fail safely without crashing server initialization
            pass

    def _save(self) -> None:
        """Persist current asks to the state file atomically."""
        if not settings.msteams_use_durable_state:
            return

        path = Path(settings.msteams_state_store_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        # Load existing state to preserve other top-level keys (e.g., approvals)
        state = {}
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    state = json.load(f)
            except Exception:
                # If existing file is corrupt, we start fresh for this write
                state = {}

        # Update asks section
        state["asks"] = {rid: ask.model_dump(mode="json") for rid, ask in self._asks.items()}

        # Atomic write using temporary file
        with tempfile.NamedTemporaryFile("w", dir=path.parent, delete=False, encoding="utf-8") as tf:
            json.dump(state, tf, indent=2)
            temp_name = tf.name

        try:
            os.replace(temp_name, path)
        except Exception as e:
            if os.path.exists(temp_name):
                os.remove(temp_name)
            raise e

    async def save(self, ask: UserAsk) -> None:
        self._asks[ask.request_id] = ask
        self._save()

    async def get(self, request_id: str) -> Optional[UserAsk]:
        return self._asks.get(request_id)

    async def update_state(self, request_id: str, state: str, reply: Optional[str] = None) -> Optional[UserAsk]:
        ask = await self.get(request_id)
        if ask:
            ask.state = state
            if reply:
                ask.reply_text = reply
            self._save()
            return ask
        return None

store = AskStore()
