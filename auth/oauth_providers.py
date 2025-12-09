"""
FastMCP Authentication Providers

OAuth provider implementations: DCR (Device Code Request) and PKCE flows.
"""

import asyncio
import secrets
import logging
from datetime import datetime
from typing import Optional, Tuple

import httpx

from .models import OAuthFlow, PKCEChallenge, DeviceCodeResponse, Token


logger = logging.getLogger(__name__)


class DCRProvider:
    """Device Code Request (DCR) flow provider."""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        auth_server_url: str,
        timeout: float = 300.0,
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.auth_server_url = auth_server_url
        self.timeout = timeout
        self._device_code_endpoint = f"{auth_server_url}/device"
        self._token_endpoint = f"{auth_server_url}/token"

    async def request_device_code(self, scope: str = "openid profile") -> DeviceCodeResponse:
        """Request device code from authorization server."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self._device_code_endpoint,
                json={
                    "client_id": self.client_id,
                    "scope": scope,
                },
                timeout=10.0
            )
            response.raise_for_status()
            data = response.json()

            return DeviceCodeResponse(
                device_code=data["device_code"],
                user_code=data["user_code"],
                verification_uri=data["verification_uri"],
                verification_uri_complete=data.get("verification_uri_complete"),
                expires_in=data.get("expires_in", 600),
                interval=data.get("interval", 5),
                message=data.get("message")
            )

    async def poll_for_token(
        self,
        device_code: str,
        issued_at: datetime,
        device_code_response: DeviceCodeResponse,
    ) -> Optional[Token]:
        """Poll authorization server for token."""
        async with httpx.AsyncClient() as client:
            while not device_code_response.is_expired(issued_at):
                try:
                    response = await client.post(
                        self._token_endpoint,
                        json={
                            "grant_type": OAuthFlow.DEVICE_CODE.value,
                            "device_code": device_code,
                            "client_id": self.client_id,
                            "client_secret": self.client_secret,
                        },
                        timeout=10.0
                    )

                    if response.status_code == 200:
                        data = response.json()
                        return Token(
                            access_token=data["access_token"],
                            token_type=data.get("token_type", "Bearer"),
                            expires_in=data.get("expires_in", 3600),
                            refresh_token=data.get("refresh_token"),
                            scope=data.get("scope")
                        )
                    elif response.status_code in (400, 401):
                        error = response.json().get("error")
                        if error == "authorization_pending":
                            await asyncio.sleep(device_code_response.interval)
                            continue
                        elif error == "slow_down":
                            await asyncio.sleep(device_code_response.interval + 5)
                            continue
                        else:
                            logger.error(f"Device code error: {error}")
                            return None

                except Exception as e:
                    logger.error(f"Error polling for token: {e}")
                    return None

        logger.error("Device code expired waiting for authorization")
        return None

    async def start_device_flow(
        self, scope: str = "openid profile"
    ) -> Optional[Tuple[str, datetime]]:
        """Start device code flow and return access token if authorized."""
        logger.info("Initiating device code flow")

        device_code_response = await self.request_device_code(scope)
        print(f"\n Device Code Authorization\n")
        print(f"  User Code:         {device_code_response.user_code}")
        verification_url = (
            device_code_response.verification_uri_complete
            or device_code_response.verification_uri
        )
        print(f"  Verification URL:  {verification_url}")
        print(f"\n  Please authorize within {device_code_response.expires_in} seconds\n")

        issued_at = datetime.utcnow()
        token = await self.poll_for_token(
            device_code_response.device_code,
            issued_at,
            device_code_response
        )

        if token:
            logger.info("Device code flow completed successfully")
            return token.access_token, issued_at
        else:
            logger.error("Device code flow failed")
            return None


class PKCEProvider:
    """PKCE (Proof Key for Code Exchange) flow provider."""

    def __init__(
        self,
        client_id: str,
        client_secret: Optional[str],
        auth_server_url: str,
        redirect_uri: str,
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.auth_server_url = auth_server_url
        self.redirect_uri = redirect_uri
        self._auth_endpoint = f"{auth_server_url}/authorize"
        self._token_endpoint = f"{auth_server_url}/token"

    def get_authorization_url(self, challenge: PKCEChallenge, state: str) -> str:
        """Get authorization URL with PKCE parameters."""
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "code_challenge": challenge.code_challenge,
            "code_challenge_method": challenge.code_challenge_method,
            "state": state,
            "scope": "openid profile"
        }
        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{self._auth_endpoint}?{query_string}"

    async def exchange_code_for_token(
        self,
        code: str,
        challenge: PKCEChallenge,
    ) -> Optional[Token]:
        """Exchange authorization code for token using PKCE."""
        async with httpx.AsyncClient() as client:
            payload = {
                "grant_type": OAuthFlow.AUTHORIZATION_CODE.value,
                "client_id": self.client_id,
                "code": code,
                "redirect_uri": self.redirect_uri,
                "code_verifier": challenge.code_verifier,
            }

            if self.client_secret:
                payload["client_secret"] = self.client_secret

            response = await client.post(
                self._token_endpoint, json=payload, timeout=10.0
            )
            response.raise_for_status()

            data = response.json()
            return Token(
                access_token=data["access_token"],
                token_type=data.get("token_type", "Bearer"),
                expires_in=data.get("expires_in", 3600),
                refresh_token=data.get("refresh_token"),
                scope=data.get("scope")
            )

    async def refresh_token(self, refresh_token: str) -> Optional[Token]:
        """Refresh access token using refresh token."""
        async with httpx.AsyncClient() as client:
            payload = {
                "grant_type": OAuthFlow.REFRESH_TOKEN.value,
                "client_id": self.client_id,
                "refresh_token": refresh_token,
            }

            if self.client_secret:
                payload["client_secret"] = self.client_secret

            response = await client.post(
                self._token_endpoint, json=payload, timeout=10.0
            )

            if response.status_code == 200:
                data = response.json()
                return Token(
                    access_token=data["access_token"],
                    token_type=data.get("token_type", "Bearer"),
                    expires_in=data.get("expires_in", 3600),
                    refresh_token=data.get("refresh_token", refresh_token),
                    scope=data.get("scope")
                )
            else:
                logger.error(f"Token refresh failed: {response.text}")
                return None
