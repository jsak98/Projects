import smtplib
import json
import os
import sys
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import urllib.request

_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _root)

from dotenv import load_dotenv
load_dotenv(os.path.join(_root, ".env"))

GMAIL_SENDER        = os.getenv("GMAIL_SENDER", "")
GMAIL_APP_PASSWORD  = os.getenv("GMAIL_APP_PASSWORD", "")
TELEGRAM_BOT_TOKEN  = os.getenv("TELEGRAM_BOT_TOKEN", "")


def send_email(to_email: str, subject: str, body: str) -> bool:
    if not GMAIL_SENDER or not GMAIL_APP_PASSWORD:
        print("Email not configured - skipping")
        return False
    if not to_email:
        print("No email address for patient - skipping")
        return False
    try:
        msg = MIMEMultipart()
        msg["Subject"] = subject
        msg["From"]    = GMAIL_SENDER
        msg["To"]      = to_email
        msg.attach(MIMEText(body, "plain"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_SENDER, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_SENDER, to_email, msg.as_string())
        print(f"Email sent to {to_email}")
        return True
    except Exception as e:
        print(f"Email failed: {e}")
        return False


def send_telegram(chat_id, message: str) -> bool:
    if not TELEGRAM_BOT_TOKEN:
        print("Telegram not configured - skipping")
        return False
    if not chat_id:
        print("No Telegram chat_id for patient - skipping")
        return False
    try:
        url     = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = json.dumps({
            "chat_id": int(chat_id),
            "text":    str(message),
        }).encode("utf-8")
        req = urllib.request.Request(
            url, data=payload,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode())
            if result.get("ok"):
                print(f"Telegram sent to {chat_id}")
                return True
            else:
                print(f"Telegram error: {result}")
                return False
    except Exception as e:
        print(f"Telegram failed: {e}")
        return False


def notify_appointment_confirmed(patient_name, patient_email, patient_phone,
                                  appt_date, time_slot, telegram_chat_id=None,
                                  clinic_name="Our Clinic"):

    date_str = appt_date.strftime("%Y/%m/%d") if hasattr(appt_date, "strftime") else str(appt_date)
    time_str = time_slot.strftime("%H:%M")     if hasattr(time_slot, "strftime") else str(time_slot)

    subject = f"Appointment Confirmed - {date_str}"
    body = (
        f"Dear {patient_name},\n\n"
        f"Your appointment has been confirmed.\n\n"
        f"Date  : {date_str}\n"
        f"Time  : {time_str}\n"
        f"Clinic: {clinic_name}\n\n"
        f"Please arrive 5 minutes before your scheduled time.\n\n"
        f"To cancel or reschedule, please call the clinic.\n\n"
        f"Regards,\n{clinic_name}"
    )
    send_email(patient_email, subject, body)
    send_telegram(telegram_chat_id, str(body))


def notify_consultation_report(patient_name, patient_email, patient_phone,
                                 visit_date, diagnosis, prescriptions,
                                 follow_up_date=None, telegram_chat_id=None,
                                 clinic_name="Our Clinic"):

    date_str = visit_date.strftime("%Y/%m/%d") if hasattr(visit_date, "strftime") else str(visit_date)

    rx_lines = ""
    for i, rx in enumerate(prescriptions, 1):
        rx_lines += (
            f"  {i}. {rx.get('medication_name','')}"
            f" | {rx.get('dosage','')}"
            f" | {rx.get('frequency','')}"
            f" | {rx.get('duration_days','?')} days\n"
        )

    follow_up_line = ""
    if follow_up_date:
        fu = follow_up_date.strftime("%d %B %Y") if hasattr(follow_up_date, "strftime") else str(follow_up_date)
        follow_up_line = f"\nFollow-up Date: {fu}\n"

    subject = f"Consultation Report - {date_str}"
    body = (
        f"Dear {patient_name},\n\n"
        f"Here is your consultation summary from {date_str} at {clinic_name}.\n\n"
        f"Diagnosis:\n{diagnosis or 'See doctor notes'}\n\n"
        f"Prescriptions:\n"
        + (rx_lines if prescriptions else "  No medications prescribed.\n") +
        f"{follow_up_line}\n"
        f"For any concerns, please contact the clinic.\n\n"
        f"Regards,\n{clinic_name}"
    )
    send_email(patient_email, subject, body)
    send_telegram(telegram_chat_id, body)
