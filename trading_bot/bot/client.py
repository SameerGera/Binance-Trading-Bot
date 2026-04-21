from __future__ import annotations

import hashlib
import hmac
import logging
import time
import urllib.parse
from dataclasses import dataclass
from typing import Any, Dict, Optional

import requests

from .exceptions import BinanceAPIError

log = logging.getLogger(__name__)


def _now_ms() -> int:
    return int(time.time() * 1000)


def _sign(query_string: str, api_secret: str) -> str:
    return hmac.new(api_secret.encode("utf-8"), query_string.encode("utf-8"), hashlib.sha256).hexdigest()


def _encode_params(params: Dict[str, Any]) -> str:
    filtered = {k: v for k, v in params.items() if v is not None}
    return urllib.parse.urlencode(filtered, doseq=True)


def _redact(params: Dict[str, Any]) -> Dict[str, Any]:
    redacted = dict(params)
    redacted.pop("signature", None)
    return redacted


@dataclass(frozen=True)
class BinanceFuturesClientConfig:
    base_url: str
    api_key: str
    api_secret: str
    recv_window: int = 5000
    timeout_s: int = 15


class BinanceFuturesClient:
    """
    Minimal REST client for Binance USDT-M Futures testnet.
    Docs endpoint used: POST /fapi/v1/order
    """

    def __init__(self, config: BinanceFuturesClientConfig):
        self._cfg = config
        self._session = requests.Session()
        self._session.headers.update({"X-MBX-APIKEY": self._cfg.api_key})

    def _request(
        self,
        method: str,
        path: str,
        *,
        signed: bool = False,
        params: Optional[Dict[str, Any]] = None,
    ) -> Any:
        params = dict(params or {})
        url = self._cfg.base_url.rstrip("/") + path

        if signed:
            params.setdefault("timestamp", _now_ms())
            params.setdefault("recvWindow", self._cfg.recv_window)
            qs = _encode_params(params)
            params["signature"] = _sign(qs, self._cfg.api_secret)

        log.info("HTTP %s %s params=%s signed=%s", method.upper(), path, _redact(params), signed)

        try:
            resp = self._session.request(
                method=method.upper(),
                url=url,
                params=params if method.upper() in {"GET", "DELETE"} else None,
                data=params if method.upper() in {"POST", "PUT"} else None,
                timeout=self._cfg.timeout_s,
            )
        except requests.RequestException:
            log.exception("Network error calling %s %s", method.upper(), path)
            raise

        content_type = resp.headers.get("Content-Type", "")
        body: Any
        if "application/json" in content_type:
            try:
                body = resp.json()
            except ValueError:
                body = resp.text
        else:
            body = resp.text

        log.info("HTTP %s %s -> %s body=%s", method.upper(), path, resp.status_code, body)

        if resp.status_code >= 400:
            raise BinanceAPIError(resp.status_code, body)
        return body

    def create_order(self, params: Dict[str, Any]) -> Any:
        return self._request("POST", "/fapi/v1/order", signed=True, params=params)

    def test_order(self, params: Dict[str, Any]) -> Any:
        return self._request("POST", "/fapi/v1/order/test", signed=True, params=params)

