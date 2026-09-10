from __future__ import annotations

import os

from fastapi import FastAPI, HTTPException

from marketplace_sms.infrai_sms import InfraiError, InfraiSmsClient
from marketplace_sms.order_handoff import HandoffResult, OrderHandoffNotifier, OrderHandoffRequest

app = FastAPI(title="Marketplace order handoff SMS")


def build_notifier() -> OrderHandoffNotifier:
    api_key = os.environ.get("INFRAI_API_KEY")
    if not api_key:
        raise RuntimeError("INFRAI_API_KEY is required")
    return OrderHandoffNotifier(InfraiSmsClient(api_key))


@app.post("/order-handoffs/notify", response_model=HandoffResult)
async def notify_order_handoff(order: OrderHandoffRequest) -> HandoffResult:
    try:
        return await build_notifier().notify(order)
    except InfraiError as exc:
        caller_status = exc.status_code if 400 <= exc.status_code < 500 else 502
        raise HTTPException(
            status_code=caller_status,
            detail={"code": exc.code, "message": str(exc)},
        ) from exc
