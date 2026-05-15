"""Сборка telegram.Bot (python-telegram-bot 20+) с опциональным HTTP/SOCKS прокси."""
from __future__ import annotations

import os
from urllib.parse import quote

from telegram import Bot
from telegram.request import HTTPXRequest


def normalize_telegram_proxy_url(raw: str | None) -> str | None:
    """Привести прокси к URL для HTTPXRequest.

    Поддержка:
    - socks5://user:pass@host:port (или http://...)
    - host:port:user:pass (формат некоторых панелей)
    """
    if not raw:
        return None
    s = raw.strip()
    if not s:
        return None
    if "://" in s:
        return s
    parts = s.split(":")
    if len(parts) == 4:
        host, port, user, password = parts
        user_q = quote(user, safe="")
        pass_q = quote(password, safe="")
        return f"socks5://{user_q}:{pass_q}@{host}:{port}"
    return s


def resolve_proxy_url() -> str | None:
    """Порядок: переменные окружения, затем config.py (если есть)."""
    raw = (os.getenv("TELEGRAM_PROXY_URL") or os.getenv("TELEGRAM_PROXY") or "").strip()
    if not raw:
        try:
            import config as _cfg

            raw = (getattr(_cfg, "TELEGRAM_PROXY_URL", None) or "").strip()
        except ImportError:
            pass
    return normalize_telegram_proxy_url(raw or None)


def create_telegram_bot(token: str, proxy_url: str | None = None) -> Bot:
    """Создать Bot; для SOCKS нужен пакет httpx[socks] (см. requirements.txt)."""
    proxy = normalize_telegram_proxy_url(proxy_url) if proxy_url else resolve_proxy_url()
    if proxy:
        request = HTTPXRequest(proxy_url=proxy)
        return Bot(token=token, request=request)
    return Bot(token=token)
