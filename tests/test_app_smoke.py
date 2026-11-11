"""End-to-end smoke tests for the web app, driven by Streamlit's AppTest.

No browser and no network: the logged-in tests put a fake client into
session state, exactly where a real login would store it.
"""

import time
from pathlib import Path

import pandas as pd
import pytest

from pyzdata.exceptions import DataFetchError
from pyzdata.run_web import _SETTINGS

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest  # noqa: E402

from pyzdata._app import _new_job  # noqa: E402

_ROOT = Path(__file__).parent.parent
_APP = str(_ROOT / "pyzdata" / "_app.py")


def test_launcher_and_checkout_settings_match():
    """`pyzdata-web` passes flags; `streamlit run app.py` reads config.toml."""
    tomllib = pytest.importorskip("tomllib")  # Python 3.11+
    toml = tomllib.loads((_ROOT / ".streamlit" / "config.toml").read_text(encoding="utf-8"))
    flat = {
        f"{section}.{name}": str(value).lower() if isinstance(value, bool) else str(value)
        for section, options in toml.items()
        for name, value in options.items()
    }
    assert flat == _SETTINGS
    assert _SETTINGS["server.address"] == "localhost"


class FakeClient:
    user_name = "Asha"

    def __init__(self, get_data=None):
        self.instruments = pd.DataFrame(
            [
                (408065, "RELIANCE", "NSE", "RELIANCE INDUSTRIES", None, 0.0, "EQ"),
                (256265, "NIFTY 50", "NSE", "NIFTY 50", None, 0.0, "EQ"),
                (884737, "NIFTY24JANFUT", "NFO", "NIFTY", "2024-01-25", 0.0, "FUT"),
            ],
            columns=[
                "instrument_token", "tradingsymbol", "exchange", "name",
                "expiry", "strike", "instrument_type",
            ],
        )
        self.requests = []
        self.closed = False
        self._get_data = get_data or (lambda: candles(3))

    def get_instrument_token(self, symbol, exchange):
        return 408065

    def get_data(self, token, start, end, interval, oi=False, progress_callback=None):
        self.requests.append({"interval": interval, "oi": oi})
        if progress_callback:
            progress_callback(1, 1)
        return self._get_data()

    def close(self):
        self.closed = True


def candles(n: int) -> pd.DataFrame:
    return pd.DataFrame({
        "tradingsymbol": "RELIANCE",
        "datetime": pd.date_range("2024-01-01", periods=n, freq="D"),
        "open": 100.0, "high": 101.0, "low": 99.0, "close": 100.5, "volume": 1000,
    })


def logged_in(client: FakeClient) -> AppTest:
    at = AppTest.from_file(_APP, default_timeout=30)
    at.session_state["client"] = client
    return at.run()


def rows_shown(at: AppTest) -> str:
    """The row count from the result caption: "3 rows · 01 Jan 2024 → …"."""
    return next(c.value for c in at.caption if " rows · " in c.value).split(" rows")[0]


def button(at: AppTest, label_start: str):
    return next(b for b in at.button if b.label.startswith(label_start))


class TestLoginScreen:

    def test_renders_enctoken_form(self):
        at = AppTest.from_file(_APP, default_timeout=30).run()
        assert not at.exception
        assert [t.label for t in at.text_input] == ["Enctoken"]

    def test_empty_submit_asks_for_input(self):
        at = AppTest.from_file(_APP, default_timeout=30).run()
        at.button[0].click().run()
        assert "fill in every field" in at.error[0].value


class TestDownloader:

    def test_download_is_disabled_until_an_instrument_is_picked(self):
        at = logged_in(FakeClient())
        assert not at.exception
        assert button(at, "Pick an instrument").disabled

    def test_full_download_flow(self):
        client = FakeClient()
        at = logged_in(client)
        at.selectbox(key="symbol_NSE").select("RELIANCE").run()
        button(at, "Download RELIANCE").click().run()

        assert not at.exception
        assert at.header[0].value == "RELIANCE"
        assert any("fetched from Zerodha in" in c.value for c in at.caption)
        assert rows_shown(at) == "3"
        assert client.requests[0]["oi"] is False

    def test_derivatives_use_word_search_and_open_interest(self):
        client = FakeClient()
        at = logged_in(client)
        at.button_group(key="exchange").select("NFO").run()
        at.text_input(key="query_NFO").input("fut nifty").run()
        at.selectbox(key="contract_NFO").select("NIFTY24JANFUT").run()
        button(at, "Download NIFTY24JANFUT").click().run()

        assert not at.exception
        assert client.requests[0]["oi"] is True

    def test_logout_is_explained(self):
        def fail():
            raise DataFetchError(
                "Zerodha logged you out while fetching RELIANCE: your session has expired "
                "(Incorrect `api_key` or `access_token`.). Log in again."
            )

        at = logged_in(FakeClient(get_data=fail))
        at.selectbox(key="symbol_NSE").select("RELIANCE").run()
        button(at, "Download RELIANCE").click().run()

        assert "logged you out" in at.error[0].value

    def test_unexpected_error_is_shown_and_the_page_recovers(self):
        """Used to leave the page stuck on a disabled "Downloading …" button."""
        def fail():
            raise RuntimeError("something nobody expected")

        at = logged_in(FakeClient(get_data=fail))
        at.selectbox(key="symbol_NSE").select("RELIANCE").run()
        button(at, "Download RELIANCE").click().run()
        at.run()  # any later interaction

        assert not at.exception
        assert "something nobody expected" in at.error[0].value
        assert "job" not in at.session_state
        assert not button(at, "Download RELIANCE").disabled

    def test_no_data_is_explained(self):
        at = logged_in(FakeClient(get_data=lambda: candles(0)))
        at.selectbox(key="symbol_NSE").select("RELIANCE").run()
        button(at, "Download RELIANCE").click().run()

        assert "no day data" in at.warning[0].value

    def test_log_out_closes_the_client_and_shows_login(self):
        client = FakeClient()
        at = logged_in(client)
        button(at, "Log out").click().run()

        assert client.closed
        assert [t.label for t in at.text_input] == ["Enctoken"]


class TestDownloadSurvivesReruns:
    """Streamlit aborts the running script whenever a new click arrives.

    The download therefore runs as a background job owned by the session,
    and every script run just attaches to it.
    """

    @staticmethod
    def _slow_job():
        def work(report):
            time.sleep(0.3)
            report(1, 1)
            return candles(4)

        return _new_job(work, "RELIANCE", "Day")

    def test_touching_another_control_mid_download_does_not_lose_it(self):
        client = FakeClient()
        at = AppTest.from_file(_APP, default_timeout=30)
        at.session_state["client"] = client
        at.session_state["job"] = self._slow_job()
        at.run()  # a rerun that is not a click on Download

        assert not at.exception
        assert at.header[0].value == "RELIANCE"
        assert rows_shown(at) == "4"
        assert client.requests == []  # attached to the running job; nothing fetched again

    def test_clicking_download_again_mid_download_does_not_fetch_twice(self):
        client = FakeClient()
        at = logged_in(client)
        at.selectbox(key="symbol_NSE").select("RELIANCE").run()
        at.session_state["job"] = self._slow_job()
        button(at, "Download RELIANCE").click().run()

        assert not at.exception
        assert client.requests == []
        assert rows_shown(at) == "4"

    def test_download_button_is_usable_again_after_the_job_finishes(self):
        def work(report):
            time.sleep(1.0)
            return candles(4)

        at = AppTest.from_file(_APP, default_timeout=30)
        at.session_state["client"] = FakeClient()
        at.session_state["job"] = _new_job(work, "RELIANCE", "Day")
        at.run()
        # after the job finished the page is redrawn with the button usable again
        assert not any(b.label.startswith("Downloading") for b in at.button)

    def test_an_error_message_survives_the_next_rerun(self):
        def fail():
            raise DataFetchError("HTTP 500 fetching RELIANCE")

        at = logged_in(FakeClient(get_data=fail))
        at.selectbox(key="symbol_NSE").select("RELIANCE").run()
        button(at, "Download RELIANCE").click().run()
        assert "Download failed" in at.error[0].value
        at.run()  # any later interaction
        assert "Download failed" in at.error[0].value

