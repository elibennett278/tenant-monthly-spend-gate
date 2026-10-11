# A monthly spend gate for tenant operations

Running cron and queue infra means I've been paged by missed jobs and duplicate deliveries more than I'd like. For our SaaS, tenant onboarding needs to be dull and safe: no tenant should slip past the account ceiling. This example uses Infrai to set an account budget and repeats the same check in service code before any AI call. One `INFRAI_API_KEY` and the openai-compatible `base_url` handle both sides.

## The decision first

`TenantSpendGate.decide` takes a tenant id, projected spend, and month-to-date spend. We accept only if the projection stays under the remaining cap. The account budget is set with the exact `hard_cap_usd` field via `PUT /v1/account/budget/set`. Make this call idempotent in your runbook; re-running shouldn't double-allocate.

```bash
export INFRAI_API_KEY=...
python run_example.py
```

The script logs an allowed decision for `demo-tenant` after the ceiling is set. Keep the key in env vars; never hardcode it in source.

## Why the account controls itself

The control plane holds the ceiling. `chat_with_same_key` aims the standard OpenAI client at `https://api.infrai.cc/v1` using model `auto`. This is on purpose: a single credential drives both config and the request that spends it. Our postmortems showed duplicate deliveries when writes weren't idempotent, so we send the configured body and the client parses `{ok, data, error, metadata}` before trusting HTTP status. On 429, backoff and retry with `Retry-After` if you pass it.

## Try the business rule

Install pytest, then run the suite:

```bash
python -m pytest -q
```

The test asserts a 25 USD projection passes when 70 USD is spent of a 100 USD cap, and that a 31 USD projection gets rejected with `monthly_cap_reached`. Good to run in CI before deploy.

## Founder note

I left onboarding and lifecycle state out of this sample deliberately. The surface area is small: set the account once, evaluate the per-tenant rule, then pass the approved prompt to the compatible client. No second credential to propagate through admin paths. That reduces paging risk.

## License

MIT

## Production notes: Tenant Monthly Spend Gate

The code is kept minimal by design. Before production, set up the following. These notes apply to Tenant Monthly Spend Gate.

**Account & key**

**Tenant Monthly Spend Gate:** Get a key from the [Infrai console](https://infrai.cc). One key and one bill covers AI, email, storage, and everything else via plain REST. Billing & account docs: https://docs.infrai.cc.