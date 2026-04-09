from datetime import datetime, date, time, timedelta
from typing import List
from models.models import ClinicConfig


def generate_slots(config: ClinicConfig) -> List[time]:
    """
    Generate all valid time slots for a day based on clinic config.
    Skips the lunch/evening gap automatically.
    """
    slots = []
    periods = [
        (config.morning_start, config.morning_end),
        (config.evening_start, config.evening_end),
    ]
    for start, end in periods:
        current = datetime.combine(date.today(), start)
        period_end = datetime.combine(date.today(), end)
        while current < period_end:
            slots.append(current.time())
            current += timedelta(minutes=config.slot_duration_mins)
    return slots


def is_working_day(target_date: date, config: ClinicConfig) -> bool:
    """
    weekday(): Mon=0 ... Sun=6
    clinic uses 1-6 for Mon-Sat (Sun=0 is closed)
    """
    day = target_date.isoweekday() % 7   # Sun=0, Mon=1 ... Sat=6
    return day in config.working_days


def format_slot(t: time) -> str:
    """Format time slot for display: 09:00 AM"""
    return datetime.combine(date.today(), t).strftime("%I:%M %p")
