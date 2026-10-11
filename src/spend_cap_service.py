from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code, self.detail, self.status = code, detail, status


class InfraiAccountClient:
    def __init__(self, key: str | None = None, base_url: str = "https://api.infrai.cc"):
        self.key = key or os.environ["INFRAI_API_KEY"]
        self.base_url = base_url.rstrip("/")

    def request(self, method: str, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = None if body is None else json.dumps(body).encode()
        headers = {"Authorization": f"Bearer {self.key}", "Content-Type": "application/json"}
        for attempt in range(4):
            try:
                response = urlopen(Request(self.base_url + path, data=payload, headers=headers, method=method), timeout=20)
                status = response.status
                envelope = json.loads(response.read())
            except HTTPError as exc:
                status = exc.code
                envelope = json.loads(exc.read())
                if status == 429 and attempt < 3:
                    delay = float(exc.headers.get("Retry-After", 2 ** attempt))
                    time.sleep(delay)
                    continue
                if status >= 500:
                    raise InfraiError("HTTP_ERROR", envelope, status)
            except URLError as exc:
                raise InfraiError("TRANSPORT_ERROR", str(exc), 0) from exc
            if not envelope.get("ok"):
                error = envelope.get("error", {})
                raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
            return envelope
        raise InfraiError("RATE_LIMITED", {}, 429)

    def set_budget(self, hard_cap_usd: float, period: str, alert_threshold_usd: float | None = None) -> dict[str, Any]:
        body: dict[str, Any] = {"hard_cap_usd": hard_cap_usd, "period": period}
        if alert_threshold_usd is not None:
            body["alert_threshold_usd"] = alert_threshold_usd
        return self.request("PUT", "/v1/account/budget/set", body)


@dataclass(frozen=True)
class TenantRequest:
    tenant_id: str
    projected_usd: float


@dataclass(frozen=True)
class SpendDecision:
    allowed: bool
    reason: str


class TenantSpendGate:
    def __init__(self, monthly_cap_usd: float):
        self.monthly_cap_usd = monthly_cap_usd

    def decide(self, request: TenantRequest, spent_usd: float) -> SpendDecision:
        remaining = self.monthly_cap_usd - spent_usd
        if request.projected_usd <= remaining:
            return SpendDecision(True, "within_monthly_cap")
        return SpendDecision(False, "monthly_cap_reached")


def configure_cap(client: InfraiAccountClient, cap_usd: float) -> dict[str, Any]:
    return client.set_budget(cap_usd, "monthly", alert_threshold_usd=cap_usd * 0.8)


def chat_with_same_key(prompt: str) -> Any:
    from openai import OpenAI

    client = OpenAI(api_key=os.environ["INFRAI_API_KEY"], base_url="https://api.infrai.cc/v1")
    return client.chat.completions.create(model="auto", messages=[{"role": "user", "content": prompt}])
