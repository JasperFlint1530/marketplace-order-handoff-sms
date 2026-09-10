import asyncio

from marketplace_sms.order_handoff import OrderHandoffNotifier, OrderHandoffRequest


class RecordingSms:
    def __init__(self) -> None:
        self.calls: list[dict[str, str]] = []

    async def send(self, *, to: str, body: str, idempotency_key: str) -> dict[str, object]:
        self.calls.append({"to": to, "body": body, "idempotency_key": idempotency_key})
        return {"message_id": "msg_1042"}


def ready_order(*, alert_sent: bool = False) -> OrderHandoffRequest:
    return OrderHandoffRequest.model_validate(
        {
            "order_id": "order-1042",
            "state": "ready_for_handoff",
            "seller": {
                "seller_name": "North Market Books",
                "pickup_location": "Counter 3",
            },
            "buyer": {"phone": "+15550101234", "handoff_alert_sent": alert_sent},
        }
    )


def test_ready_order_sends_one_buyer_handoff_alert() -> None:
    sms = RecordingSms()

    result = asyncio.run(OrderHandoffNotifier(sms).notify(ready_order()))

    assert result.action == "sent"
    assert result.message_id == "msg_1042"
    assert sms.calls == [
        {
            "to": "+15550101234",
            "body": "Order order-1042 is ready from North Market Books. Pickup: Counter 3",
            "idempotency_key": "order-handoff:order-1042:ready",
        }
    ]


def test_recorded_buyer_update_prevents_duplicate_alert() -> None:
    sms = RecordingSms()

    result = asyncio.run(OrderHandoffNotifier(sms).notify(ready_order(alert_sent=True)))

    assert result.action == "already_notified"
    assert sms.calls == []
