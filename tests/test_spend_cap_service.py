from src.spend_cap_service import TenantRequest, TenantSpendGate


def test_tenant_request_is_rejected_when_projection_crosses_cap():
    gate = TenantSpendGate(monthly_cap_usd=100)
    assert gate.decide(TenantRequest("acme", 25), spent_usd=70).allowed is True
    decision = gate.decide(TenantRequest("acme", 31), spent_usd=70)
    assert decision.allowed is False
    assert decision.reason == "monthly_cap_reached"
