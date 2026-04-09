from datetime import date, time
from typing import List, Optional
from models.models import Appointment, BlockedSlot, ClinicConfig
from db.connection import DBConn


class AppointmentRepository:

    def has_active_appointment(self, patient_id: int, appt_date: date) -> bool:
        """Check if patient already has a pending/confirmed booking on this date."""
        with DBConn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT COUNT(*) FROM appointments
                    WHERE patient_id = %s
                      AND appointment_date = %s
                      AND status IN ('pending', 'confirmed')
                """, (patient_id, appt_date))
                return cur.fetchone()[0] > 0

    def is_slot_taken(self, appt_date: date, time_slot: time) -> bool:
        """Check if a specific slot is already booked."""
        with DBConn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT COUNT(*) FROM appointments
                    WHERE appointment_date = %s
                      AND time_slot = %s
                      AND status IN ('pending', 'confirmed')
                """, (appt_date, time_slot))
                return cur.fetchone()[0] > 0

    def get_booked_slots(self, appt_date: date) -> List[time]:
        """Return all taken slots on a given date."""
        with DBConn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT time_slot FROM appointments
                    WHERE appointment_date = %s
                      AND status IN ('pending', 'confirmed')
                """, (appt_date,))
                return [row[0] for row in cur.fetchall()]

    def get_blocked_slots(self, appt_date: date) -> List[BlockedSlot]:
        with DBConn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, block_date, start_time, end_time, reason
                    FROM blocked_slots WHERE block_date = %s
                """, (appt_date,))
                return [
                    BlockedSlot(id=r[0], block_date=r[1], start_time=r[2],
                                end_time=r[3], reason=r[4])
                    for r in cur.fetchall()
                ]

    def get_by_date(self, appt_date: date) -> List[dict]:
        """Get all appointments for a date with patient name joined."""
        with DBConn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT a.id, a.patient_id, p.full_name, p.phone,
                           a.appointment_date, a.time_slot, a.reason,
                           a.status, a.requested_via, a.notes
                    FROM appointments a
                    JOIN patients p ON p.id = a.patient_id
                    WHERE a.appointment_date = %s
                    ORDER BY a.time_slot
                """, (appt_date,))
                cols = ['id','patient_id','full_name','phone','appointment_date',
                        'time_slot','reason','status','requested_via','notes']
                return [dict(zip(cols, row)) for row in cur.fetchall()]

    def get_by_patient(self, patient_id: int) -> List[dict]:
        with DBConn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, appointment_date, time_slot, reason, status, notes
                    FROM appointments WHERE patient_id = %s
                    ORDER BY appointment_date DESC, time_slot DESC
                """, (patient_id,))
                cols = ['id','appointment_date','time_slot','reason','status','notes']
                return [dict(zip(cols, row)) for row in cur.fetchall()]

    def create(self, a: Appointment) -> Appointment:
        with DBConn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO appointments
                        (patient_id, doctor_id, appointment_date, time_slot,
                         reason, status, requested_via, notes)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                    RETURNING id, created_at
                """, (
                    a.patient_id, a.doctor_id, a.appointment_date, a.time_slot,
                    a.reason, a.status, a.requested_via, a.notes
                ))
                row = cur.fetchone()
                a.id = row[0]
                a.created_at = row[1]
                return a

    def update_status(self, appt_id: int, status: str, notes: str = None):
        with DBConn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE appointments
                    SET status = %s, notes = COALESCE(%s, notes), updated_at = NOW()
                    WHERE id = %s
                """, (status, notes, appt_id))

    def get_clinic_config(self) -> ClinicConfig:
        with DBConn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM clinic_config LIMIT 1")
                row = cur.fetchone()
                return ClinicConfig(
                    id=row[0], slot_duration_mins=row[1],
                    morning_start=row[2], morning_end=row[3],
                    evening_start=row[4], evening_end=row[5],
                    working_days=list(row[6])
                )

    def add_blocked_slot(self, b: BlockedSlot):
        with DBConn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO blocked_slots (block_date, start_time, end_time, reason)
                    VALUES (%s, %s, %s, %s)
                """, (b.block_date, b.start_time, b.end_time, b.reason))

    def get_pending_form_requests(self) -> List[dict]:
        """Google Forms sync — get all appointments requested via form, still pending."""
        with DBConn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT a.id, p.full_name, p.phone, a.appointment_date,
                           a.time_slot, a.reason, a.status
                    FROM appointments a
                    JOIN patients p ON p.id = a.patient_id
                    WHERE a.requested_via = 'google_form'
                      AND a.status = 'pending'
                    ORDER BY a.appointment_date, a.time_slot
                """)
                cols = ['id','full_name','phone','appointment_date','time_slot','reason','status']
                return [dict(zip(cols, row)) for row in cur.fetchall()]
