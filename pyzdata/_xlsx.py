"""A small, fast ``.xlsx`` writer for candle data — standard library only.

Why not ``DataFrame.to_excel``?  openpyxl and xlsxwriter both build a Python
object for every cell.  For a year of 1-minute candles (~92k rows) that took
5 s, for five years 25 s — long enough to look like a hang.  An ``.xlsx`` file
is just a zip of XML, so this module streams the sheet XML straight into the
zip instead: ~1 s for 460k rows, in bounded memory, and one dependency fewer.

Scope: plain numpy-backed columns as the downloader produces them — text,
numbers and naive datetimes.  One sheet, no formatting beyond date-times.
"""

from __future__ import annotations

import io
import zipfile
from typing import List
from xml.sax.saxutils import escape

import pandas as pd
from pandas.api.types import is_bool_dtype, is_datetime64_dtype, is_numeric_dtype

#: Excel worksheets hold 1,048,576 rows including the header.
EXCEL_MAX_ROWS = 1_048_575

_EXCEL_EPOCH = pd.Timestamp("1899-12-30")  # day 0 of Excel's date serial numbers
_XML = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
_MAIN = 'xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"'
_PKG = "http://schemas.openxmlformats.org/package/2006"
_DOC = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml"

# Everything in the workbook except the sheet itself never changes.
_FIXED_PARTS = {
    "[Content_Types].xml": (
        f'<Types xmlns="{_PKG}/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        f'<Override PartName="/xl/workbook.xml" ContentType="{_TYPE}.sheet.main+xml"/>'
        f'<Override PartName="/xl/worksheets/sheet1.xml" ContentType="{_TYPE}.worksheet+xml"/>'
        f'<Override PartName="/xl/styles.xml" ContentType="{_TYPE}.styles+xml"/></Types>'
    ),
    "_rels/.rels": (
        f'<Relationships xmlns="{_PKG}/relationships">'
        f'<Relationship Id="rId1" Type="{_DOC}/officeDocument" Target="xl/workbook.xml"/></Relationships>'
    ),
    "xl/workbook.xml": (
        f'<workbook {_MAIN} xmlns:r="{_DOC}">'
        '<sheets><sheet name="data" sheetId="1" r:id="rId1"/></sheets></workbook>'
    ),
    "xl/_rels/workbook.xml.rels": (
        f'<Relationships xmlns="{_PKG}/relationships">'
        f'<Relationship Id="rId1" Type="{_DOC}/worksheet" Target="worksheets/sheet1.xml"/>'
        f'<Relationship Id="rId2" Type="{_DOC}/styles" Target="styles.xml"/></Relationships>'
    ),
    # Cell style 0 = general, cell style 1 = date-time.
    "xl/styles.xml": (
        f'<styleSheet {_MAIN}>'
        '<numFmts count="1"><numFmt numFmtId="164" formatCode="yyyy-mm-dd hh:mm:ss"/></numFmts>'
        '<fonts count="1"><font><sz val="11"/><name val="Calibri"/></font></fonts>'
        '<fills count="2"><fill><patternFill patternType="none"/></fill>'
        '<fill><patternFill patternType="gray125"/></fill></fills>'
        '<borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>'
        '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
        '<cellXfs count="2"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>'
        '<xf numFmtId="164" fontId="0" fillId="0" borderId="0" xfId="0" applyNumberFormat="1"/></cellXfs>'
        '<cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>'
        '</styleSheet>'
    ),
}

_BLANK = "<c/>"


def _text_cell(value: object) -> str:
    return f'<c t="inlineStr"><is><t>{escape(str(value))}</t></is></c>'


def _cells(column: pd.Series) -> List[str]:
    """One XML cell per value of *column*."""
    if is_datetime64_dtype(column):
        column, style = (column - _EXCEL_EPOCH) / pd.Timedelta(days=1), ' s="1"'
    elif is_numeric_dtype(column) and not is_bool_dtype(column):
        style = ""
    else:
        # Text repeats a lot (the symbol is the same on every row), so build
        # each distinct cell once.
        values = column.astype(object).where(column.notna(), None)
        xml = {v: _BLANK if v is None else _text_cell(v) for v in values.unique()}
        return [xml[v] for v in values.tolist()]
    # `v == v` is False only for NaN / NaT.
    return [f"<c{style}><v>{v!r}</v></c>" if v == v else _BLANK for v in column.tolist()]


def to_excel_bytes(df: pd.DataFrame, chunk_rows: int = 50_000) -> bytes:
    """Serialise *df* as an ``.xlsx`` workbook with a single sheet, ``data``.

    Rows are written *chunk_rows* at a time so memory stays flat however
    large the frame is.
    """
    if len(df) > EXCEL_MAX_ROWS:
        raise ValueError(f"Excel holds at most {EXCEL_MAX_ROWS:,} rows; got {len(df):,}. Use CSV.")

    # Date-times need a wider column or Excel shows "########".
    widths = "".join(
        f'<col min="{i}" max="{i}" width="20" customWidth="1"/>'
        for i, name in enumerate(df.columns, start=1)
        if is_datetime64_dtype(df[name])
    )
    header = "".join(_text_cell(name) for name in df.columns)

    buffer = io.BytesIO()
    # compresslevel=1: the XML is very repetitive, so higher levels cost
    # seconds and save little.
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED, compresslevel=1) as book:
        for name, xml in _FIXED_PARTS.items():
            book.writestr(name, _XML + xml)
        with book.open("xl/worksheets/sheet1.xml", "w") as sheet:
            sheet.write(
                f"{_XML}<worksheet {_MAIN}>{f'<cols>{widths}</cols>' if widths else ''}"
                f"<sheetData><row>{header}</row>".encode()
            )
            for start in range(0, len(df), chunk_rows):
                part = df.iloc[start:start + chunk_rows]
                columns = [_cells(part[name]) for name in part.columns]
                sheet.write(
                    "".join(f"<row>{''.join(cells)}</row>" for cells in zip(*columns)).encode()
                )
            sheet.write(b"</sheetData></worksheet>")
    return buffer.getvalue()
