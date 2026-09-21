"""Tests for pyzdata._xlsx — the dependency-free Excel writer."""

import io
import sys
import time
import zipfile

import numpy as np
import pandas as pd
import pytest

from pyzdata._xlsx import EXCEL_MAX_ROWS, to_excel_bytes


def _candles(n: int) -> pd.DataFrame:
    return pd.DataFrame({
        "tradingsymbol": "NIFTY 50",
        "datetime": pd.date_range("2024-01-01 09:15", periods=n, freq="min"),
        "close": np.arange(n) + 0.25,
        "volume": np.arange(n),
    })


def _read(raw: bytes) -> pd.DataFrame:
    """Read the workbook back with an independent implementation."""
    pytest.importorskip("openpyxl")
    return pd.read_excel(io.BytesIO(raw))


class TestToExcelBytes:

    def test_round_trip(self):
        df = _candles(5)
        back = _read(to_excel_bytes(df))
        assert list(back.columns) == list(df.columns)
        assert back["tradingsymbol"].tolist() == ["NIFTY 50"] * 5
        assert back["close"].tolist() == df["close"].tolist()
        assert back["volume"].tolist() == df["volume"].tolist()

    def test_datetimes_are_real_excel_dates(self):
        df = _candles(400)  # crosses midnight-free minutes; fractions of a day
        back = _read(to_excel_bytes(df))
        assert pd.api.types.is_datetime64_any_dtype(back["datetime"])
        assert (back["datetime"].dt.round("s").values == df["datetime"].values).all()

    def test_text_with_xml_special_characters(self):
        df = _candles(2).assign(tradingsymbol=["M&M", "<A> \"B\""])
        assert _read(to_excel_bytes(df))["tradingsymbol"].tolist() == ["M&M", "<A> \"B\""]

    def test_missing_values_become_blank_cells(self):
        df = _candles(3).assign(open_interest=[1.0, np.nan, 3.0], note=["a", None, "c"])
        back = _read(to_excel_bytes(df))
        assert back["open_interest"].isna().tolist() == [False, True, False]
        assert back["note"].isna().tolist() == [False, True, False]

    def test_every_row_is_written_when_the_frame_spans_chunks(self):
        df = _candles(2_500)
        back = _read(to_excel_bytes(df, chunk_rows=1_000))
        assert back["volume"].tolist() == list(range(2_500))

    def test_needs_no_excel_library(self, monkeypatch):
        monkeypatch.setitem(sys.modules, "openpyxl", None)
        monkeypatch.setitem(sys.modules, "xlsxwriter", None)
        parts = zipfile.ZipFile(io.BytesIO(to_excel_bytes(_candles(3)))).namelist()
        assert "xl/worksheets/sheet1.xml" in parts

    def test_large_frames_are_fast(self):
        """A year of 1-minute candles took ~5 s with openpyxl; keep it snappy."""
        df = _candles(200_000)
        start = time.perf_counter()
        to_excel_bytes(df)
        assert time.perf_counter() - start < 5

    def test_too_many_rows_for_excel_is_an_error(self):
        df = pd.DataFrame({"n": np.zeros(EXCEL_MAX_ROWS + 1, dtype="int8")})
        with pytest.raises(ValueError, match="1,048,575"):
            to_excel_bytes(df)
