"""Send alerts to a Telegram chat (or print them when no bot is configured)."""

import json
import logging
import urllib.request

log = logging.getLogger(__name__)


class Notifier:
    def __init__(self, bot_token: str | None, chat_id: str | None) -> None:
        self.bot_token = bot_token
        self.chat_id = chat_id

    @property
    def enabled(self) -> bool:
        return bool(self.bot_token and self.chat_id)

    def send(self, text: str) -> None:
        if not self.enabled:
            print(text)
            return
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{self.bot_token}/sendMessage",
            data=json.dumps({"chat_id": self.chat_id, "text": text, "disable_web_page_preview": True}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            urllib.request.urlopen(req, timeout=20).read()
        except Exception:
            log.exception("Telegram send failed; message was:\n%s", text)
