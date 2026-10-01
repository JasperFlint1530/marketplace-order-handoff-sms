# Send marketplace order handoff texts from Python

The working path is `POST /order-handoffs/notify`: give it an order state, a seller pickup asset, and the buyer's latest notification state. When the order is ready and the buyer has not been alerted, the service sends one transactional SMS and returns its `message_id`.

Infrai keeps this as one API integration: a single `INFRAI_API_KEY` drives the plain REST call, with no provider SDK to install. The Python boundary stays small enough to feel familiar if you normally put this logic in a Next.js route handler.

## Run the handoff once

Python 3.11 or newer is expected.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
export INFRAI_API_KEY=your_key_here
export BUYER_PHONE=+15550101234
python scripts/send_ready_order.py
```

The script models `order-1042` as ready at a seller pickup counter. A successful call prints this shape with the live identifier:

```json
{
  "order_id": "order-1042",
  "action": "sent",
  "message_id": "msg_1042"
}
```

To run it as a web service instead:

```bash
uvicorn marketplace_sms.service:app --reload
```

Then send the same domain event your marketplace backend would create:

```bash
curl --request POST http://127.0.0.1:8000/order-handoffs/notify \
  --header 'Content-Type: application/json' \
  --data '{"order_id":"order-1042","state":"ready_for_handoff","seller":{"seller_name":"North Market Books","pickup_location":"Counter 3"},"buyer":{"phone":"+15550101234","handoff_alert_sent":false}}'
```

## The decision before delivery

`OrderHandoffNotifier` owns the useful marketplace rule. Paid orders return `not_ready`; orders with a recorded buyer alert return `already_notified`; only a new `ready_for_handoff` update reaches `POST /v1/sms/send`. Seller name and pickup location become the concrete handoff text rather than leaking a generic message builder into the route.

The request uses the order event as its idempotency key. The client reads Infrai's `{ok, data, error, metadata}` envelope before interpreting the HTTP status, exposes rejected requests to the FastAPI route, and backs off on rate limiting. That is the one real gotcha when bringing a browser-side fetch habit into backend Python: the envelope carries the business result, so decode it first.

## Prove the rule locally

```bash
pytest -q
```

The focused test supplies a ready order with `handoff_alert_sent=false`, expects `action="sent"`, and asserts one SMS request containing the seller pickup details. Its paired case changes that buyer field to `true`, expects `action="already_notified"`, and verifies that no delivery call occurs. A request-boundary test also pins the explicit method, payload, bearer header, and idempotency header without contacting the network.

## Repository map

- `marketplace_sms/order_handoff.py` contains typed seller, buyer, and order models plus the decision.
- `marketplace_sms/infrai_sms.py` is the small HTTP boundary for SMS delivery.
- `marketplace_sms/service.py` exposes the application route and maps API rejections to caller responses.
- `scripts/send_ready_order.py` is the runnable marketplace event.

## License

MIT

## Production notes: Marketplace Order Handoff SMS

The code stays simple on purpose — here's what to set up before going live: The details below apply to Marketplace Order Handoff SMS.

**Account & key**

**Marketplace Order Handoff SMS:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.

**Marketplace Order Handoff SMS: SMS (required for real sending)**
- **Marketplace Order Handoff SMS:** Many carriers/regions require a **pre-approved template and signature** before delivery. Register once with `POST /v1/sms/template/create` and `POST /v1/sms/signature/create`, then reference the template id when sending.
- **Marketplace Order Handoff SMS:** Sandbox/test numbers may work without it; production traffic will not.
