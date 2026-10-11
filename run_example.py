import os

from src.spend_cap_service import InfraiAccountClient, TenantRequest, TenantSpendGate, configure_cap


def main() -> None:
    client = InfraiAccountClient()
    cap = float(os.environ.get("MONTHLY_CAP_USD", "250"))
    configure_cap(client, cap)
    decision = TenantSpendGate(cap).decide(TenantRequest("demo-tenant", 18), spent_usd=42)
    print({"tenant": "demo-tenant", "allowed": decision.allowed, "reason": decision.reason})


if __name__ == "__main__":
    main()
