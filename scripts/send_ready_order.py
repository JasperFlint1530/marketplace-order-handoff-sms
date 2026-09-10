import asyncio
import os

from marketplace_sms.infrai_sms import InfraiSmsClient
from marketplace_sms.order_handoff import OrderHandoffNotifier, OrderHandoffRequest


async def main() -> None:
    api_key = os.environ.get("INFRAI_API_KEY")
    buyer_phone = os.environ.get("BUYER_PHONE")
    if not api_key or not buyer_phone:
        raise SystemExit("Set INFRAI_API_KEY and BUYER_PHONE")

    order = OrderHandoffRequest.model_validate(
        {
            "order_id": "order-1042",
            "state": "ready_for_handoff",
            "seller": {
                "seller_name": "North Market Books",
                "pickup_location": "Counter 3, 18 River Street",
            },
            "buyer": {"phone": buyer_phone, "handoff_alert_sent": False},
        }
    )
    result = await OrderHandoffNotifier(InfraiSmsClient(api_key)).notify(order)
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    asyncio.run(main())
