import json
import logging
from datetime import date, timedelta
from typing import Optional

import gspread
from google.oauth2.service_account import Credentials

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
HEADERS = ["Sana", "Turi", "Kategoriya", "Summa", "Valyuta", "Izoh", "Mahsulot", "Miqdor", "Birlik narxi"]
COLUMN_WIDTHS = [100, 90, 150, 110, 90, 200, 150, 80, 110]
NUMBER_FORMAT_COLUMNS = [3, 7, 8]  # Summa, Miqdor, Birlik narxi
HEADER_COLOR = {"red": 0.180, "green": 0.490, "blue": 0.196}
BAND_COLOR = {"red": 0.910, "green": 0.961, "blue": 0.914}
SHEET_ROWS = 1000
SHEETS_EPOCH = date(1899, 12, 30)


class SheetsService:
    def __init__(
        self,
        spreadsheet_id: str,
        credentials_path: Optional[str] = None,
        credentials_json: Optional[str] = None,
    ):
        if credentials_json:
            info = json.loads(credentials_json)
            creds = Credentials.from_service_account_info(info, scopes=SCOPES)
        elif credentials_path:
            creds = Credentials.from_service_account_file(credentials_path, scopes=SCOPES)
        else:
            raise RuntimeError(
                "Google hisob ma'lumotlari topilmadi: GOOGLE_CREDENTIALS_JSON yoki "
                "GOOGLE_CREDENTIALS_PATH'dan birini belgilang."
            )
        self.client = gspread.authorize(creds)
        self.spreadsheet = self.client.open_by_key(spreadsheet_id)

    def _get_or_create_worksheet(self, chat_id: int):
        title = f"user_{chat_id}"
        try:
            worksheet = self.spreadsheet.worksheet(title)
            self._ensure_headers(worksheet)
            return worksheet
        except gspread.WorksheetNotFound:
            worksheet = self.spreadsheet.add_worksheet(title=title, rows=SHEET_ROWS, cols=len(HEADERS))
            worksheet.append_row(HEADERS)
            self._apply_pretty_format(worksheet)
            return worksheet

    def _ensure_headers(self, worksheet) -> None:
        """Kengaytiriladigan (backward-compatible) sxema: eski varaqlarga faqat yetishmayotgan
        ustunlarni oxiriga qo'shadi, mavjud ma'lumotlarga tegmaydi."""
        current = worksheet.row_values(1)
        if current == HEADERS:
            return
        if current and HEADERS[: len(current)] == current and len(current) < len(HEADERS):
            worksheet.update(values=[HEADERS], range_name="A1")
            self._extend_header_style(worksheet, len(current))

    def _extend_header_style(self, worksheet, start_col_index: int) -> None:
        sheet_id = worksheet.id
        requests = [
            {
                "repeatCell": {
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": 0,
                        "endRowIndex": 1,
                        "startColumnIndex": start_col_index,
                        "endColumnIndex": len(HEADERS),
                    },
                    "cell": {
                        "userEnteredFormat": {
                            "backgroundColor": HEADER_COLOR,
                            "horizontalAlignment": "CENTER",
                            "textFormat": {
                                "foregroundColor": {"red": 1, "green": 1, "blue": 1},
                                "bold": True,
                                "fontSize": 11,
                            },
                        }
                    },
                    "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)",
                }
            }
        ]
        for col_index in range(start_col_index, len(HEADERS)):
            requests.append(
                {
                    "updateDimensionProperties": {
                        "range": {
                            "sheetId": sheet_id,
                            "dimension": "COLUMNS",
                            "startIndex": col_index,
                            "endIndex": col_index + 1,
                        },
                        "properties": {"pixelSize": COLUMN_WIDTHS[col_index]},
                        "fields": "pixelSize",
                    }
                }
            )
        try:
            self.spreadsheet.batch_update({"requests": requests})
        except Exception:
            logger.warning("Sarlavha dizaynini kengaytirishda xatolik (funksionallikka ta'sir qilmaydi)")

    def _apply_pretty_format(self, worksheet) -> None:
        sheet_id = worksheet.id
        requests = [
            {
                "updateSheetProperties": {
                    "properties": {
                        "sheetId": sheet_id,
                        "gridProperties": {"frozenRowCount": 1},
                        "tabColor": HEADER_COLOR,
                    },
                    "fields": "gridProperties.frozenRowCount,tabColor",
                }
            },
            {
                "repeatCell": {
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": 0,
                        "endRowIndex": 1,
                        "startColumnIndex": 0,
                        "endColumnIndex": len(HEADERS),
                    },
                    "cell": {
                        "userEnteredFormat": {
                            "backgroundColor": HEADER_COLOR,
                            "horizontalAlignment": "CENTER",
                            "textFormat": {
                                "foregroundColor": {"red": 1, "green": 1, "blue": 1},
                                "bold": True,
                                "fontSize": 11,
                            },
                        }
                    },
                    "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)",
                }
            },
            {
                "addBanding": {
                    "bandedRange": {
                        "range": {
                            "sheetId": sheet_id,
                            "startRowIndex": 0,
                            "endRowIndex": SHEET_ROWS,
                            "startColumnIndex": 0,
                            "endColumnIndex": len(HEADERS),
                        },
                        "rowProperties": {
                            "headerColor": HEADER_COLOR,
                            "firstBandColor": {"red": 1, "green": 1, "blue": 1},
                            "secondBandColor": BAND_COLOR,
                        },
                    }
                }
            },
            {
                "setBasicFilter": {
                    "filter": {
                        "range": {
                            "sheetId": sheet_id,
                            "startRowIndex": 0,
                            "endRowIndex": SHEET_ROWS,
                            "startColumnIndex": 0,
                            "endColumnIndex": len(HEADERS),
                        }
                    }
                }
            },
        ]
        for col_index in NUMBER_FORMAT_COLUMNS:
            requests.append(
                {
                    "repeatCell": {
                        "range": {
                            "sheetId": sheet_id,
                            "startRowIndex": 1,
                            "endRowIndex": SHEET_ROWS,
                            "startColumnIndex": col_index,
                            "endColumnIndex": col_index + 1,
                        },
                        "cell": {"userEnteredFormat": {"numberFormat": {"type": "NUMBER", "pattern": "#,##0"}}},
                        "fields": "userEnteredFormat.numberFormat",
                    }
                }
            )
        for col_index, width in enumerate(COLUMN_WIDTHS):
            requests.append(
                {
                    "updateDimensionProperties": {
                        "range": {
                            "sheetId": sheet_id,
                            "dimension": "COLUMNS",
                            "startIndex": col_index,
                            "endIndex": col_index + 1,
                        },
                        "properties": {"pixelSize": width},
                        "fields": "pixelSize",
                    }
                }
            )
        self.spreadsheet.batch_update({"requests": requests})

    def append_record(self, chat_id: int, record: dict) -> None:
        worksheet = self._get_or_create_worksheet(chat_id)
        row = [
            record.get("date", ""),
            record.get("type", ""),
            record.get("category", ""),
            record.get("amount", ""),
            record.get("currency", ""),
            record.get("description", ""),
            record.get("product", ""),
            record.get("quantity", ""),
            record.get("unit_price", ""),
        ]
        worksheet.append_row(row, value_input_option="USER_ENTERED")

    def get_records(self, chat_id: int) -> list[dict]:
        worksheet = self._get_or_create_worksheet(chat_id)
        records = worksheet.get_all_records(value_render_option=gspread.utils.ValueRenderOption.unformatted)
        for record in records:
            sana = record.get("Sana")
            if isinstance(sana, (int, float)):
                record["Sana"] = (SHEETS_EPOCH + timedelta(days=int(sana))).isoformat()
        return records
