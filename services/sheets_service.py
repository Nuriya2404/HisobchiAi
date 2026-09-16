import json
from typing import Optional

import gspread
from google.oauth2.service_account import Credentials

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
HEADERS = ["Sana", "Turi", "Kategoriya", "Summa", "Valyuta", "Izoh"]
COLUMN_WIDTHS = [100, 90, 160, 110, 90, 280]
HEADER_COLOR = {"red": 0.180, "green": 0.490, "blue": 0.196}
BAND_COLOR = {"red": 0.910, "green": 0.961, "blue": 0.914}
SHEET_ROWS = 1000


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
            return self.spreadsheet.worksheet(title)
        except gspread.WorksheetNotFound:
            worksheet = self.spreadsheet.add_worksheet(title=title, rows=SHEET_ROWS, cols=len(HEADERS))
            worksheet.append_row(HEADERS)
            self._apply_pretty_format(worksheet)
            return worksheet

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
                "repeatCell": {
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": 1,
                        "endRowIndex": SHEET_ROWS,
                        "startColumnIndex": 3,
                        "endColumnIndex": 4,
                    },
                    "cell": {"userEnteredFormat": {"numberFormat": {"type": "NUMBER", "pattern": "#,##0"}}},
                    "fields": "userEnteredFormat.numberFormat",
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
        ]
        worksheet.append_row(row, value_input_option="USER_ENTERED")

    def get_records(self, chat_id: int) -> list[dict]:
        worksheet = self._get_or_create_worksheet(chat_id)
        return worksheet.get_all_records()
