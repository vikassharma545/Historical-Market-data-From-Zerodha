"""Unit tests for KiteAuth."""

from unittest.mock import MagicMock

import pytest
import requests

from pyzdata.auth import KiteAuth
from pyzdata.exceptions import AuthenticationError

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _resp(status_code: int, json_data: dict = None, cookies: dict = None):
    """Build a mock ``requests.Response``."""
    r = MagicMock(spec=requests.Response)
    r.status_code = status_code
    r.json.return_value = json_data or {}
    r.cookies = cookies or {}
    if status_code >= 400:
        http_err = requests.HTTPError(response=r)
        r.raise_for_status.side_effect = http_err
    else:
        r.raise_for_status.return_value = None
    return r


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def auth(mock_session, config):
    return KiteAuth(mock_session, config)


# ---------------------------------------------------------------------------
# login_with_credentials
# ---------------------------------------------------------------------------

class TestLoginWithCredentials:

    def _step1_ok(self, user_id="AB1234"):
        return _resp(
            200,
            {"status": "success", "data": {"request_id": "req123", "user_id": user_id}},
        )

    def _step2_ok(self, enctoken="abc.def.ghi"):
        r = _resp(200, {"status": "success"})
        r.cookies = {"enctoken": enctoken}
        return r

    def test_success_returns_enctoken(self, auth, mock_session):
        mock_session.post.side_effect = [self._step1_ok(), self._step2_ok()]

        token = auth.login_with_credentials("AB1234", "secret", "123456")

        assert token == "abc.def.ghi"
        assert mock_session.post.call_count == 2

    def test_step1_http_403_raises(self, auth, mock_session):
        mock_session.post.return_value = _resp(403)

        with pytest.raises(AuthenticationError, match="HTTP 403"):
            auth.login_with_credentials("AB1234", "bad_pw", "000000")

    def test_step1_api_rejects_raises(self, auth, mock_session):
        mock_session.post.return_value = _resp(
            200, {"status": "error", "message": "Invalid credentials"}
        )

        with pytest.raises(AuthenticationError, match="Invalid credentials"):
            auth.login_with_credentials("AB1234", "bad", "000000")

    def test_step2_http_error_raises(self, auth, mock_session):
        mock_session.post.side_effect = [self._step1_ok(), _resp(401)]

        with pytest.raises(AuthenticationError, match="HTTP 401"):
            auth.login_with_credentials("AB1234", "secret", "999999")

    def test_step2_missing_enctoken_raises(self, auth, mock_session):
        step2 = _resp(200, {"status": "success"})
        step2.cookies = {}  # no enctoken cookie
        mock_session.post.side_effect = [self._step1_ok(), step2]

        with pytest.raises(AuthenticationError, match="enctoken"):
            auth.login_with_credentials("AB1234", "secret", "123456")

    def test_totp_int_is_stringified(self, auth, mock_session):
        """Integer TOTP must be converted to str — leading zeros must be safe."""
        mock_session.post.side_effect = [self._step1_ok(), self._step2_ok()]

        auth.login_with_credentials("AB1234", "pw", 123456)  # int, not str

        _, kwargs = mock_session.post.call_args_list[1]
        assert kwargs["data"]["twofa_value"] == "123456"

    def test_network_error_step1_raises(self, auth, mock_session):
        mock_session.post.side_effect = requests.ConnectionError("unreachable")

        with pytest.raises(AuthenticationError, match="Network error"):
            auth.login_with_credentials("AB1234", "pw", "000000")


# ---------------------------------------------------------------------------
# make_auth_headers
# ---------------------------------------------------------------------------

class TestMakeAuthHeaders:

    def test_format(self):
        headers = KiteAuth.make_auth_headers("mytoken123")
        assert headers == {"Authorization": "enctoken mytoken123"}

    def test_different_tokens_produce_different_headers(self):
        assert KiteAuth.make_auth_headers("a") != KiteAuth.make_auth_headers("b")
