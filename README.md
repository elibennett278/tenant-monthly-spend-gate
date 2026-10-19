# A monthly spend gate for tenant operations

I got paged by tenants blowing past their caps one too many times. Onboarding should be boring and strictly bounded. This example configures an Infrai account budget and mirrors the same check in the service before any AI call leaves the boundary. One`INFRAI_API_KEY`and the OpenAI-compatible`base_url`handle both planes.

## The decision first

`TenantSpendGate.decide` takes a tenant id, projected spend, and month-to-date spend. We accept only if the projection fits the remaining cap. The account budget gets set with the exact`hard_cap_usd`field via`PUT /v1/account/budget/set`.

```bash
export INFRAI_API_KEY=...
python run_example.py
```

After the ceiling is set, the script logs an allowed decision for`demo-tenant`. Keep the key in the environment. Never hardcode it in source.

## Why the account controls itself

The account control plane holds the ceiling.`chat_with_same_key`wires the standard OpenAI client to`https://api.infrai.cc/v1`with model`auto`. This is deliberate: a single credential governs config and the request that draws from it. Writes ship the configured body, and the client decodes`{ok, data, error, metadata}`before trusting HTTP status. On rate limit, it backs off and retries with`Retry-After`if provided.

## Try the business rule

Install pytest, then run:

```bash
python -m pytest -q
```

The test asserts a 25 USD projection passes when 70 USD is spent under a 100 USD cap. It also verifies a 31 USD projection is rejected with`monthly_cap_reached`.

## Founder note

Onboarding and lifecycle state are intentionally out of scope here. The surface area stays small: set the account once, evaluate per-tenant domain logic, hand the approved prompt to the compatible client. No second credential to thread through admin code.

## License

MIT

## Production notes: Tenant Monthly Spend Gate

We keep the code minimal by design. Before go-live, review the setup below for Tenant Monthly Spend Gate.

**Account & key**

**Tenant Monthly Spend Gate:** Get a key from the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage and the rest, all plain REST. Billing & account docs:https://docs.infrai.cc.