"""Управление аккаунтами Telegram и прокси."""
import re
from typing import Optional
from ..config import load_accounts, save_accounts

PROXY_SCHEMES = {"http", "https", "socks4", "socks5"}


def parse_proxy(proxy_str: str) -> Optional[dict]:
    """
    Форматы:
      scheme://ip:port
      scheme://user:pass@ip:port
    Возвращает dict для pyrogram `proxy` параметра или None.
    """
    proxy_str = (proxy_str or "").strip()
    if not proxy_str:
        return None
    m = re.match(
        r"(?P<scheme>\w+)://(?:(?P<user>[^:]+):(?P<pwd>[^@]+)@)?(?P<host>[\w.\-]+):(?P<port>\d+)$",
        proxy_str,
    )
    if not m:
        raise ValueError(f"Неверный формат прокси: {proxy_str!r}")
    scheme = m.group("scheme").lower()
    if scheme not in PROXY_SCHEMES:
        raise ValueError(f"Схема прокси должна быть одной из {PROXY_SCHEMES}")
    proxy = {
        "scheme": scheme,
        "hostname": m.group("host"),
        "port": int(m.group("port")),
    }
    if m.group("user"):
        proxy["username"] = m.group("user")
        proxy["password"] = m.group("pwd")
    return proxy


class AccountManager:
    """CRUD-менеджер аккаунтов (session name + proxy)."""

    def __init__(self) -> None:
        self.accounts: list[dict] = load_accounts()

    def _persist(self) -> None:
        save_accounts(self.accounts)

    def all(self) -> list[dict]:
        return list(self.accounts)

    def get(self, account_id: str) -> Optional[dict]:
        for a in self.accounts:
            if a["id"] == account_id:
                return a
        return None

    def add(self, name: str, session_name: str, proxy: str = "") -> dict:
        # уникальный id
        import uuid
        acc = {
            "id": uuid.uuid4().hex[:8],
            "name": name.strip() or session_name,
            "session": session_name.strip(),
            "proxy": proxy.strip(),
        }
        self.accounts.append(acc)
        self._persist()
        return acc

    def remove(self, account_id: str) -> bool:
        before = len(self.accounts)
        self.accounts = [a for a in self.accounts if a["id"] != account_id]
        if len(self.accounts) < before:
            self._persist()
            return True
        return False

    def update_proxy(self, account_id: str, proxy: str) -> None:
        acc = self.get(account_id)
        if acc:
            acc["proxy"] = proxy.strip()
            self._persist()
