import asyncio

import httpx

from marketplace_sms.infrai_sms import InfraiSmsClient


def test_sms_request_uses_contract_and_idempotency_header() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/v1/sms/send"
        assert request.headers["Authorization"] == "Bearer test-key"
        assert request.headers["Idempotency-Key"] == "order-handoff:order-1042:ready"
        assert request.content == b'{"to":"+15550101234","body":"Pickup at Counter 3"}'
        return httpx.Response(200, json={"ok": True, "data": {"message_id": "msg_1042"}, "metadata": {}})

    client = InfraiSmsClient("test-key", transport=httpx.MockTransport(handler))
    data = asyncio.run(
        client.send(
            to="+15550101234",
            body="Pickup at Counter 3",
            idempotency_key="order-handoff:order-1042:ready",
        )
    )

    assert data["message_id"] == "msg_1042"
