from dataclasses import dataclass, field
from datetime import date, time, datetime
from typing import Optional, List


@dataclass
class User:
    id: int
    name: str
    email: str
    role: str                        # doctor | nurse | receptionist
    is_active: bool = True
    created_at: Optional[datetime] = None


@dataclass
class Patient:
    id: Optional[int]
    full_name: str
    phone: str
    dob: Optional[date] = None
    gender: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    blood_type: Optional[str] = None
    allergies: Optional[str] = None
    chronic_conditions: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    insurance_provider: Optional[str] = None
    insurance_id: Optional[str] = None
    consent_given_at: Optional[datetime] = None
    telegram_chat_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class Consultation:
    id: Optional[int]
    patient_id: int
    doctor_id: int
    visit_date: date
    chief_complaint: Optional[str] = None
    clinical_notes: Optional[str] = None
    diagnosis: Optional[str] = None
    tests_ordered: Optional[str] = None
    follow_up_date: Optional[date] = None
    created_at: Optional[datetime] = None


@dataclass
class Prescription:
    id: Optional[int]
    consultation_id: int
    patient_id: int
    medication_name: str
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    duration_days: Optional[int] = None
    instructions: Optional[str] = None
    refills_allowed: int = 0
    created_at: Optional[datetime] = None


@dataclass
class Appointment:
    id: Optional[int]
    patient_id: int
    appointment_date: date
    time_slot: time
    status: str = 'pending'          # pending | confirmed | completed | cancelled
    doctor_id: Optional[int] = None
    reason: Optional[str] = None
    requested_via: str = 'manual'    # manual | google_form
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class BlockedSlot:
    id: Optional[int]
    block_date: date
    start_time: time
    end_time: time
    reason: str = 'blocked'


@dataclass
class ClinicConfig:
    id: int = 1
    slot_duration_mins: int = 10
    morning_start: time = time(9, 0)
    morning_end: time = time(13, 0)
    evening_start: time = time(14, 0)
    evening_end: time = time(18, 0)
    working_days: List[int] = field(default_factory=lambda: [1,2,3,4,5,6])
