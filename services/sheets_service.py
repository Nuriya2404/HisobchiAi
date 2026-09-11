import gspread
from google.oauth2.service_account import Credentials

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
HEADERS = ["Sana", "Turi", "Kategoriya", "Summa", "Valyuta", "Izoh"]


class SheetsService:
    def __init__(self, credentials_path: str, spreadsheet_id: str):
        creds = Credentials.from_service_account_file(credentials_path, scopes=SCOPES)
        self.client = gspread.authorize(creds)
        self.spreadsheet = self.client.open_by_key(spreadsheet_id)

    def _get_or_create_worksheet(self, chat_id: int):
        title = f"user_{chat_id}"
        try:
            return self.spreadsheet.worksheet(title)
        except gspread.WorksheetNotFound:
            worksheet = self.spreadsheet.add_worksheet(title=title, rows=1000, cols=len(HEADERS))
            worksheet.append_row(HEADERS)
            return worksheet

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
