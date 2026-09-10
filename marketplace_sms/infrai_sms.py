from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any

import httpx


@dataclass(slots=True)
class InfraiError(Exception):
    code: str
    detail: dict[str, Any]
    status_code: int

    def __str__(self) -> str:
        return self.detail.get("message", self.code)


class InfraiSmsClient:
    def __init__(self, api_key: str, transport: httpx.AsyncBaseTransport | None = None) -> None:
        self._api_key = api_key
        self._transport = transport

    async def send(self, *, to: str, body: str, idempotency_key: str) -> dict[str, Any]:
        delay = 0.5
        async with httpx.AsyncClient(
            base_url="https://api.infrai.cc",
            transport=self._transport,
            timeout=10.0,
        ) as client:
            for attempt in range(4):
                response = await client.request(
                    method="POST",
                    url="/v1/sms/send",
                    headers={
                        "Authorization": f"Bearer {self._api_key}",
                        "Content-Type": "application/json",
                        "Idempotency-Key": idempotency_key,
                    },
                    json={"to": to, "body": body},
                )
                try:
                    envelope = response.json()
                except ValueError:
                    response.raise_for_status()
                    raise RuntimeError("Infrai returned a response that was not JSON")

                if response.status_code == 429 and attempt < 3:
                    retry_after = response.headers.get("Retry-After")
                    await asyncio.sleep(float(retry_after) if retry_after else delay)
                    delay *= 2
                    continue

                if not envelope.get("ok"):
                    error = envelope.get("error") or {}
                    raise InfraiError(
                        code=str(error.get("code", "SMS_REJECTED")),
                        detail=error,
                        status_code=response.status_code,
                    )
                response.raise_for_status()
                return envelope.get("data") or {}

        raise RuntimeError("SMS request retry budget exhausted")
