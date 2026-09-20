"""Unit tests for the PyZData facade."""

from unittest.mock import MagicMock, patch

import pytest
import requests

from pyzdata import PyZData
from pyzdata.exceptions import AuthenticationError, ConfigurationError


def _resp(status_code: int, json_data: dict = None, text: str = ""):
    r = MagicMock(spec=requests.Response)
    r.status_code = status_code
    r.json.return_value = json_data or {}
    r.text = text
    if status_code >= 400:
        r.raise_for_status.side_effect = requests.HTTPError(response=r)
    else:
        r.raise_for_status.return_value = None
    return r


@pytest.fixture
def session(config, instruments_csv_text):
    """A session whose GET serves the profile and the instruments CSV."""
    s = MagicMock(spec=requests.Session)
    s.profile = _resp(200, {"status": "success", "data": {"user_id": "AB1234", "user_name": "Asha"}})

    def _get(url, **kwargs):
        if url == config.profile_url:
            return s.profile
        return _resp(200, text=instruments_csv_text)

    s.get.side_effect = _get
    with patch("pyzdata.client._build_session", return_value=s):
        yield s


class TestEnctokenLogin:

    def test_valid_token_exposes_user_name(self, session, config):
        client = PyZData(enctoken="good", config=config)
        assert client.user_name == "Asha"

    def test_user_name_falls_back_to_user_id(self, session, config):
        session.profile = _resp(200, {"status": "success", "data": {"user_id": "AB1234"}})
        client = PyZData(enctoken="good", config=config)
        assert client.user_name == "AB1234"

    def test_invalid_token_fails_at_construction(self, session, config):
        session.profile = _resp(403)
        with pytest.raises(AuthenticationError, match="Invalid or expired enctoken"):
            PyZData(enctoken="bad", config=config)
        session.close.assert_called_once()

    def test_no_credentials_raises_configuration_error(self, session, config):
        with pytest.raises(ConfigurationError):
            PyZData(config=config)


class TestInstrumentsProperty:

    def test_returns_the_instruments_master(self, session, config):
        client = PyZData(enctoken="good", config=config)
        assert "RELIANCE" in client.instruments["tradingsymbol"].tolist()

    def test_lookup_works_end_to_end(self, session, config):
        client = PyZData(enctoken="good", config=config)
        assert client.get_instrument_token("reliance", "NSE") == 408065
