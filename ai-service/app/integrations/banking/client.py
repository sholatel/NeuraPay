"""
HTTP client for the NestJS banking backend.

Architecture constraint: this class is the ONLY place in the entire AI service
that constructs HTTP requests to the banking backend. Every agent tool must call
methods on this client — never use httpx directly in tool code.

NestJS global prefix: /api
All routes below are relative to that prefix.
"""

import httpx

from app.core.exceptions import BankingBackendError
from app.core.logging import get_logger

logger = get_logger(__name__)

# NestJS global API prefix (set in main.ts)
_API_PREFIX = "/api"

# Conversion factor: the NestJS backend stores and accepts amounts in kobo.
# 1 NGN = 100 kobo. Users speak in NGN; we convert before sending to the API.
_KOBO_PER_NGN = 100


def ngn_to_kobo(amount_ngn: float) -> int:
    """Convert user-facing Naira amount to kobo integer for the banking API."""
    return int(round(amount_ngn * _KOBO_PER_NGN))


def kobo_to_ngn(amount_kobo: int) -> float:
    """Convert kobo integer from the banking API to user-facing Naira."""
    return amount_kobo / _KOBO_PER_NGN


class BankingClient:
    """
    Async HTTP client wrapping the NestJS banking backend.

    One instance is created per request (in `build_banking_client()`),
    so the bearer token is always scoped to the authenticated user.
    """

    def __init__(
        self,
        base_url: str,
        timeout: int = 30,
        bearer_token: str | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/") + _API_PREFIX
        self._timeout = timeout
        self._headers: dict[str, str] = {"Content-Type": "application/json"}
        if bearer_token:
            self._headers["Authorization"] = f"Bearer {bearer_token}"

    # ── Wallet endpoints ──────────────────────────────────────────────────────

    async def get_all_wallets(self) -> dict:
        """GET /api/wallet — returns all wallets with computed balances."""
        return await self._get("/wallet")

    async def get_balance(self, user_id: str, currency: str = "NGN") -> dict:
        """GET /api/wallet/:userId/balance?currency=NGN"""
        return await self._get(
            f"/wallet/{user_id}/balance",
            params={"currency": currency.upper()},
        )

    async def get_transactions(
        self,
        currency: str = "NGN",
        page: int = 1,
        limit: int = 10,
    ) -> dict:
        """GET /api/transactions/history — paginated ledger for the authenticated user."""
        return await self._get(
            "/transactions/history",
            params={
                "currency": currency.upper(),
                "page": page,
                "limit": min(limit, 100),  # backend max is 100
            },
        )

    async def transfer(
        self,
        to_user_id: str,
        amount_ngn: float,
        reference: str,
        currency: str = "NGN",
    ) -> dict:
        """
        POST /api/wallet/transfer

        Amounts are converted from NGN to kobo before sending to the backend.
        The `reference` must be unique (8–100 chars) — callers must generate it.
        """
        return await self._post(
            "/wallet/transfer",
            {
                "toUserId": to_user_id,
                "amount": ngn_to_kobo(amount_ngn),
                "currency": currency.upper(),
                "reference": reference,
            },
        )

    async def deposit(
        self,
        amount_ngn: float,
        reference: str,
        currency: str = "NGN",
    ) -> dict:
        """
        POST /api/wallet/deposit

        Amounts are converted from NGN to kobo before sending to the backend.
        """
        return await self._post(
            "/wallet/deposit",
            {
                "amount": ngn_to_kobo(amount_ngn),
                "currency": currency.upper(),
                "reference": reference,
            },
        )

    # ── Private HTTP helpers ──────────────────────────────────────────────────

    async def _get(self, path: str, params: dict | None = None) -> dict:
        url = f"{self._base_url}{path}"
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(url, headers=self._headers, params=params)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as exc:
            self._raise_backend_error(exc, url)
        except httpx.RequestError as exc:
            logger.error("banking_client.connection_error", url=url, error=str(exc))
            raise BankingBackendError(
                "Could not reach the banking backend. Is the NestJS service running on port 3000?",
                detail=str(exc),
            ) from exc

    async def _post(self, path: str, payload: dict) -> dict:
        url = f"{self._base_url}{path}"
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(url, headers=self._headers, json=payload)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as exc:
            self._raise_backend_error(exc, url)
        except httpx.RequestError as exc:
            logger.error("banking_client.connection_error", url=url, error=str(exc))
            raise BankingBackendError(
                "Could not reach the banking backend. Is the NestJS service running on port 3000?",
                detail=str(exc),
            ) from exc

    def _raise_backend_error(self, exc: httpx.HTTPStatusError, url: str) -> None:
        status = exc.response.status_code
        logger.error("banking_client.http_error", url=url, status=status)

        # Surface meaningful messages for common status codes.
        try:
            body = exc.response.json()
            detail = body.get("message", exc.response.text)
        except Exception:
            detail = exc.response.text

        if status == 401:
            raise BankingBackendError(
                "Authentication failed. Please log in again.", detail=detail
            ) from exc
        if status == 403:
            raise BankingBackendError(
                "Account is not active. Please contact support.", detail=detail
            ) from exc
        if status == 404:
            raise BankingBackendError(
                "The requested resource was not found.", detail=detail
            ) from exc
        if status == 409:
            raise BankingBackendError(
                "This transaction reference has already been used.", detail=detail
            ) from exc
        raise BankingBackendError(
            f"Banking backend returned an error ({status}).", detail=detail
        ) from exc
