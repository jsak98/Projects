"""
Google Sheets → DB sync for appointment form requests.

Setup:
1. Share your Google Sheet with the service account email
2. Put credentials.json in the project root
3. Set GOOGLE_SHEET_ID in .env
4. Run: python google_sheets/sync.py (or call sync_form_requests() on a schedule)
"""
import os
from datetime import datetime, date, time
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

from services.appointment_service import AppointmentService
from services.patient_service import PatientService

load_dotenv()

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.readonly"
]

SHEET_ID = os.getenv("GOOGLE_SHEET_ID", "")

# Expected Google Form column order (adjust to match your form):
# Timestamp | Full Name | Phone | Preferred Date | Preferred Time | Reason
COL_TIMESTAMP   = 0
COL_NAME        = 1
COL_PHONE       = 2
COL_DATE        = 3
COL_TIME        = 4
COL_REASON      = 5
COL_STATUS      = 6   # We write back to this column: 'synced' / 'duplicate' / 'error'


def get_sheet():
    creds = Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
    client = gspread.authorize(creds)
    return client.open_by_key(SHEET_ID).sheet1


def parse_date(date_str: str) -> date:
    for fmt in ('%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y', '%m/%d/%Y'):
        try:
            return datetime.strptime(date_str.strip(), fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Cannot parse date: {date_str}")


def parse_time(time_str: str) -> time:
    for fmt in ('%H:%M', '%I:%M %p', '%I:%M%p'):
        try:
            return datetime.strptime(time_str.strip(), fmt).time()
        except ValueError:
            continue
    raise ValueError(f"Cannot parse time: {time_str}")


def sync_form_requests():
    """
    Pull new rows from Google Sheet and insert as pending appointments.
    Writes sync status back to the sheet (column 7).
    """
    patient_svc = PatientService()
    appt_svc    = AppointmentService()

    sheet = get_sheet()
    rows  = sheet.get_all_values()
    header = rows[0]
    data_rows = rows[1:]

    for i, row in enumerate(data_rows, start=2):   # start=2 because row 1 is header
        # Skip already processed rows
        if len(row) > COL_STATUS and row[COL_STATUS] in ('synced', 'duplicate', 'error'):
            continue

        try:
            name   = row[COL_NAME].strip()
            phone  = row[COL_PHONE].strip()
            appt_date = parse_date(row[COL_DATE])
            appt_time = parse_time(row[COL_TIME])
            reason = row[COL_REASON].strip() if len(row) > COL_REASON else ''

            # Find or flag patient
            search_result = patient_svc.search(phone)
            if not search_result.success or not search_result.data:
                sheet.update_cell(i, COL_STATUS + 1, f'error: patient not found ({phone})')
                continue

            patient = search_result.data[0]

            # Try to book
            result = appt_svc.book(
                patient_id=patient.id,
                appt_date=appt_date,
                time_slot=appt_time,
                reason=reason,
                requested_via='google_form',
            )

            if result.success:
                sheet.update_cell(i, COL_STATUS + 1, 'synced')
            elif 'already has an active appointment' in result.message:
                sheet.update_cell(i, COL_STATUS + 1, 'duplicate')
            elif 'already taken' in result.message:
                sheet.update_cell(i, COL_STATUS + 1, 'slot_taken - needs reassignment')
            else:
                sheet.update_cell(i, COL_STATUS + 1, f'error: {result.message}')

        except Exception as e:
            sheet.update_cell(i, COL_STATUS + 1, f'error: {str(e)}')

    print("Sync complete.")


if __name__ == "__main__":
    sync_form_requests()
