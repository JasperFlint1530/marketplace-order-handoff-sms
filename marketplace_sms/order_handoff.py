from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class OrderState(StrEnum):
    PAID = "paid"
    READY_FOR_HANDOFF = "ready_for_handoff"
    HANDED_OFF = "handed_off"


class SellerAsset(BaseModel):
    seller_name: str = Field(min_length=1, max_length=80)
    pickup_location: str = Field(min_length=1, max_length=160)


class BuyerUpdate(BaseModel):
    phone: str = Field(pattern=r"^\+[1-9]\d{7,14}$")
    handoff_alert_sent: bool = False


class OrderHandoffRequest(BaseModel):
    order_id: str = Field(min_length=1, max_length=64)
    state: OrderState
    seller: SellerAsset
    buyer: BuyerUpdate


class HandoffResult(BaseModel):
    order_id: str
    action: str
    message_id: str | None = None


@dataclass(slots=True)
class OrderHandoffNotifier:
    sms: Any

    async def notify(self, order: OrderHandoffRequest) -> HandoffResult:
        if order.state != OrderState.READY_FOR_HANDOFF:
            return HandoffResult(order_id=order.order_id, action="not_ready")
        if order.buyer.handoff_alert_sent:
            return HandoffResult(order_id=order.order_id, action="already_notified")

        body = (
            f"Order {order.order_id} is ready from {order.seller.seller_name}. "
            f"Pickup: {order.seller.pickup_location}"
        )
        data = await self.sms.send(
            to=order.buyer.phone,
            body=body,
            idempotency_key=f"order-handoff:{order.order_id}:ready",
        )
        return HandoffResult(
            order_id=order.order_id,
            action="sent",
            message_id=str(data["message_id"]),
        )
