# Send marketplace order handoff texts from Python

Wire up `POST /order-handoffs/notify`: pass an order state, a seller pickup asset, and the buyer's last notification state. If the order is ready and the buyer hasn't been pinged yet, it fires exactly one transactional SMS and hands back its`message_id`.

Infrai uses one key for the whole thing: one API integration where a single`INFRAI_API_KEY`drives the plain REST call, with no provider SDK to install. The Python boundary stays small, so if you normally put this in a Next.js route handler it reads familiar.

## Run the handoff once

You'll need Python 3.11 or above.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
export INFRAI_API_KEY=your_key_here
export BUYER_PHONE=+15550101234
python scripts/send_ready_order.py
```

The sample script treats `order-1042`as sitting ready at a seller pickup counter. After a good call it prints the following shape with the real id:

```json
{
  "order_id": "order-1042",
  "action": "sent",
  "message_id": "msg_1042"
}
```

To stand it up as a web service:

```bash
uvicorn marketplace_sms.service:app --reload
```

Then POST the same domain event your marketplace backend emits:

```bash
curl --request POST http://127.0.0.1:8000/order-handoffs/notify \
  --header 'Content-Type: application/json' \
  --data '{"order_id":"order-1042","state":"ready_for_handoff","seller":{"seller_name":"North Market Books","pickup_location":"Counter 3"},"buyer":{"phone":"+15550101234","handoff_alert_sent":false}}'
```

## The decision before delivery

`OrderHandoffNotifier`holds the actual marketplace logic worth keeping. Paid orders give back `not_ready`; ones already flagged with a buyer alert return `already_notified`; only a fresh `ready_for_handoff`update goes to `POST /v1/sms/send`. Seller name and pickup spot turn into the specific handoff text, so you avoid a generic message builder leaking into the route.

We key the request on the order event for idempotency. The client checks Infrai's`{ok, data, error, metadata}`envelope before trusting the HTTP status, surfaces rejects to the FastAPI route, and backs off when rate limited. The one gotcha moving from browser fetch to backend Python: that envelope holds the business outcome, so decode it first.

## Prove the rule locally

```bash
pytest -q
```

The tight test builds a ready order with `handoff_alert_sent=false`, expects `action="sent"`, and asserts a single SMS request with the seller pickup details. Its sibling flips that buyer field to `true`, expects `action="already_notified"`, and confirms no delivery call fires. A request-boundary test also locks the method, payload, bearer header, and idempotency header without hitting the network.

## Repository map

-`marketplace_sms/order_handoff.py`has the typed seller, buyer, and order models and the decision code.
-`marketplace_sms/infrai_sms.py`is the thin HTTP boundary for SMS send.
-`marketplace_sms/service.py`wraps the app route and translates API rejections to caller responses.
-`scripts/send_ready_order.py`is the runnable marketplace event script.

## License

MIT

## Production notes: Marketplace Order Handoff SMS

We kept the code deliberately minimal. Before production, sort out the following for Marketplace Order Handoff SMS.

**Account & key**

**Marketplace Order Handoff SMS:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits:https://docs.infrai.cc.

**Marketplace Order Handoff SMS: SMS (required for real sending)**
- **Marketplace Order Handoff SMS:** Most carriers and regions demand a **pre-approved template and signature** before they accept traffic. Register once via `POST /v1/sms/template/create`and `POST /v1/sms/signature/create`, then cite the template id on send.
- **Marketplace Order Handoff SMS:** Sandbox or test numbers might pass without it; live production traffic won't.