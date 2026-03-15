"""Zerodha Kite authentication.

Handles the two-step login flow (credentials + TOTP) and exposes a static
helper for constructing authorisation headers from a pre-obtained enctoken.

Design decisions
----------------
* ``KiteAuth`` is injected with a ``requests.Session`` rather than creating
  its own, so the retry strategy configured in ``PyZData`` applies here too.
* TOTP is always coerced to ``str`` before sending.  Passing an ``int`` like
  ``123456`` is safe, but ``012345`` as an int would silently become ``12345``
  and fail — string coercion prevents that bug.
* Each login step raises :class:`~pyzdata.exceptions.AuthenticationError`
  with a human-readable message so callers don't have to parse HTTP exceptions.
"""

from __future__ import annotations

import logging
from typing import Dict

import requests

from .config import Config
from .exceptions import AuthenticationError

logger = logging.getLogger(__name__)


class KiteAuth:
    """Performs the Zerodha two-step credential login."""

    def __init__(self, session: requests.Session, config: Config) -> None:
        self._session = session
        self._config = config

    # ---------------------------------------------------------------- public

    def login_with_credentials(
        self, user_id: str, password: str, totp: str
    ) -> str:
        """Execute the two-step Kite login and return the ``enctoken`` string.

        Parameters
        ----------
        user_id:
            Zerodha client ID (e.g. ``"AB1234"``).
        password:
            Account password.
        totp:
            Current TOTP code.  Passed as a string to preserve leading zeros.

        Returns
        -------
        str
            The ``enctoken`` to use in subsequent API calls.

        Raises
        ------
        AuthenticationError
            On any network failure, HTTP error, or missing enctoken cookie.
        """
        logger.info("Logging in as %s …", user_id)
        request_id = self._step1_login(user_id, password)
        enctoken = self._step2_twofa(user_id, request_id, str(totp))
        logger.info("Login successful for %s", user_id)
        return enctoken

    @staticmethod
    def make_auth_headers(enctoken: str) -> Dict[str, str]:
        """Return the Authorization header dict for Kite API calls."""
        return {"Authorization": f"enctoken {enctoken}"}

    # --------------------------------------------------------------- private

    def _step1_login(self, user_id: str, password: str) -> str:
        """POST credentials and return the ``request_id`` for step 2."""
        try:
            resp = self._session.post(
                self._config.login_url,
                data={"user_id": user_id, "password": password},
                timeout=self._config.request_timeout,
            )
            resp.raise_for_status()
        except requests.HTTPError as exc:
            raise AuthenticationError(
                f"Login failed (HTTP {exc.response.status_code}). "
                "Check your user_id and password."
            ) from exc
        except requests.RequestException as exc:
            raise AuthenticationError(
                f"Network error during login: {exc}"
            ) from exc

        payload = resp.json()
        if payload.get("status") != "success":
            raise AuthenticationError(
                f"Login rejected by Kite: {payload.get('message', 'no message')}"
            )

        return payload["data"]["request_id"]

    def _step2_twofa(self, user_id: str, request_id: str, totp: str) -> str:
        """POST the TOTP and return the ``enctoken`` from the response cookie."""
        try:
            resp = self._session.post(
                self._config.twofa_url,
                data={
                    "request_id": request_id,
                    "twofa_value": totp,
                    "user_id": user_id,
                },
                timeout=self._config.request_timeout,
            )
            resp.raise_for_status()
        except requests.HTTPError as exc:
            raise AuthenticationError(
                f"2FA failed (HTTP {exc.response.status_code}). "
                "Check your TOTP value."
            ) from exc
        except requests.RequestException as exc:
            raise AuthenticationError(
                f"Network error during 2FA: {exc}"
            ) from exc

        try:
            payload = resp.json()
        except Exception:
            payload = {}
        if payload.get("status") != "success":
            raise AuthenticationError(
                f"2FA rejected by Kite: {payload.get('message', 'Invalid TOTP or session expired')}"
            )

        enctoken = resp.cookies.get("enctoken")
        if not enctoken:
            raise AuthenticationError(
                "2FA succeeded but the enctoken cookie was not set. "
                "Your TOTP may be incorrect or expired."
            )
        return enctoken
