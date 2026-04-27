"""
Sandbox API integration for PAN-Aadhaar-Name verification.

This module is wired with placeholder credentials so the architecture is
ready. When the real Sandbox.co.in account is provisioned, set:
  SANDBOX_API_KEY, SANDBOX_API_SECRET, SANDBOX_BASE_URL
in backend/.env and the verification will use the real API.

While placeholders are set, verify_pan returns a deterministic stub
result based on simple format validation so the UI flow is testable
end-to-end.
"""
import os
import re
import logging
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

PAN_REGEX = re.compile(r"^[A-Z]{5}[0-9]{4}[A-Z]$")
AADHAAR_REGEX = re.compile(r"^\d{12}$")


def _is_placeholder() -> bool:
    key = os.environ.get("SANDBOX_API_KEY", "")
    return not key or key.startswith("placeholder")


async def _fetch_sandbox_token() -> Optional[str]:
    """Authenticate with Sandbox API and return access token."""
    base = os.environ.get("SANDBOX_BASE_URL", "https://api.sandbox.co.in")
    key = os.environ.get("SANDBOX_API_KEY")
    secret = os.environ.get("SANDBOX_API_SECRET")
    try:
        async with httpx.AsyncClient(timeout=15) as cli:
            r = await cli.post(
                f"{base}/authenticate",
                headers={"x-api-key": key, "x-api-secret": secret, "x-api-version": "1.0"},
            )
            r.raise_for_status()
            return r.json().get("access_token")
    except Exception as e:
        logger.warning(f"Sandbox auth failed: {e}")
        return None


async def verify_pan(pan: str, name: str) -> dict:
    """
    Verify a PAN number against name. Returns:
      { verified: bool, status: str, name_match: bool, raw: dict, mode: 'live'|'stub' }
    """
    pan = (pan or "").upper().strip()
    if not PAN_REGEX.match(pan):
        return {"verified": False, "status": "invalid_format", "name_match": False, "raw": {}, "mode": "stub"}

    if _is_placeholder():
        # Deterministic stub — passes format check, returns "verified=False" so admin
        # knows verification needs real keys, but doesn't block the UI.
        return {
            "verified": False,
            "status": "placeholder_keys",
            "name_match": False,
            "raw": {"message": "Sandbox API placeholder credentials in use. Set SANDBOX_API_KEY in .env to enable live verification."},
            "mode": "stub",
        }

    token = await _fetch_sandbox_token()
    if not token:
        return {"verified": False, "status": "auth_failed", "name_match": False, "raw": {}, "mode": "live"}

    base = os.environ.get("SANDBOX_BASE_URL", "https://api.sandbox.co.in")
    try:
        async with httpx.AsyncClient(timeout=20) as cli:
            r = await cli.post(
                f"{base}/kyc/pan/verify",
                headers={
                    "Authorization": token,
                    "x-api-key": os.environ.get("SANDBOX_API_KEY"),
                    "x-api-version": "1.0",
                },
                json={"pan": pan, "name_as_per_pan": name, "consent": "Y", "reason": "NGO 80G donor verification"},
            )
            data = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
            verified = bool(data.get("data", {}).get("status") == "valid")
            name_match = bool(data.get("data", {}).get("name_match", False))
            return {"verified": verified, "status": data.get("data", {}).get("status", "unknown"),
                    "name_match": name_match, "raw": data, "mode": "live"}
    except Exception as e:
        logger.warning(f"Sandbox PAN verify failed: {e}")
        return {"verified": False, "status": "api_error", "name_match": False, "raw": {"error": str(e)}, "mode": "live"}


async def verify_aadhaar_pan_link(pan: str, aadhaar: str) -> dict:
    """Check if a PAN is linked to the given Aadhaar (Sandbox API)."""
    pan = (pan or "").upper().strip()
    aadhaar = re.sub(r"\D", "", aadhaar or "")
    if not PAN_REGEX.match(pan) or not AADHAAR_REGEX.match(aadhaar):
        return {"linked": False, "status": "invalid_format", "mode": "stub"}

    if _is_placeholder():
        return {"linked": False, "status": "placeholder_keys", "mode": "stub",
                "raw": {"message": "Set SANDBOX_API_KEY/SECRET in .env for live PAN-Aadhaar link verification."}}

    token = await _fetch_sandbox_token()
    if not token:
        return {"linked": False, "status": "auth_failed", "mode": "live"}

    base = os.environ.get("SANDBOX_BASE_URL", "https://api.sandbox.co.in")
    try:
        async with httpx.AsyncClient(timeout=20) as cli:
            r = await cli.post(
                f"{base}/kyc/pan-aadhaar/status",
                headers={"Authorization": token, "x-api-key": os.environ.get("SANDBOX_API_KEY"), "x-api-version": "1.0"},
                json={"pan": pan, "aadhaar_number": aadhaar, "consent": "Y", "reason": "NGO donor verification"},
            )
            data = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
            return {"linked": bool(data.get("data", {}).get("aadhaar_seeding_status") == "linked"),
                    "status": data.get("data", {}).get("aadhaar_seeding_status", "unknown"),
                    "raw": data, "mode": "live"}
    except Exception as e:
        logger.warning(f"Sandbox link check failed: {e}")
        return {"linked": False, "status": "api_error", "raw": {"error": str(e)}, "mode": "live"}
