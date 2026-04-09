from datetime import date, time
from typing import List
from models.models import Appointment, BlockedSlot
from repositories.appointment_repo import AppointmentRepository
from repositories.audit_repo import AuditRepository
from utils.result import Result
from utils.slot_generator import generate_slots, is_working_day, format_slot


class AppointmentService:

    def __init__(self):
        self.repo = AppointmentRepository()
        self.audit = AuditRepository()

    def get_available_slots(self, target_date: date) -> Result:
        """Return all free, unblocked slots for a given date."""
        try:
            config = self.repo.get_clinic_config()

            # Rule 1: No Sundays / non-working days
            if not is_working_day(target_date, config):
                return Result.fail("Clinic is closed on this day")

            # Generate all theoretically valid slots
            all_slots = generate_slots(config)

            # Remove booked slots
            booked = set(self.repo.get_booked_slots(target_date))

            # Remove blocked slots (lunch, meetings, etc.)
            blocked_ranges = self.repo.get_blocked_slots(target_date)

            def is_blocked(slot: time) -> bool:
                for b in blocked_ranges:
                    if b.start_time <= slot < b.end_time:
                        return True
                return False

            available = [s for s in all_slots if s not in booked and not is_blocked(s)]
            return Result.ok(data=available)

        except Exception as e:
            return Result.fail(f"Could not load slots: {e}")

    def book(self, patient_id: int, appt_date: date,
             time_slot: time, reason: str = None,
             requested_via: str = 'manual',
             status: str = 'pending',
             doctor_id: int = None,
             user_id: int = None) -> Result:
        try:
            config = self.repo.get_clinic_config()

            # Rule 1: Working day check
            if not is_working_day(appt_date, config):
                return Result.fail("Cannot book — clinic is closed on this day")

            # Rule 2: No active appointment for same patient on same day
            if self.repo.has_active_appointment(patient_id, appt_date):
                return Result.fail(
                    "This patient already has an active appointment on this date. "
                    "Cancel or complete it first, or choose a different date."
                )

            # Rule 3: Slot must not be taken by another patient
            if self.repo.is_slot_taken(appt_date, time_slot):
                return Result.fail(
                    f"Slot {format_slot(time_slot)} on {appt_date} is already taken. "
                    "Please choose another slot."
                )

            appt = Appointment(
                id=None,
                patient_id=patient_id,
                doctor_id=doctor_id,
                appointment_date=appt_date,
                time_slot=time_slot,
                reason=reason,
                status=status,
                requested_via=requested_via,
            )
            created = self.repo.create(appt)
            self.audit.log(user_id, 'CREATE', 'appointments', created.id,
                           f"Booked {appt_date} {format_slot(time_slot)} for patient {patient_id}")
            return Result.ok(data=created, message=f"Appointment booked for {format_slot(time_slot)}")

        except Exception as e:
            # Catch DB-level unique constraint violations as a safety net
            if 'unique_slot' in str(e):
                return Result.fail("Slot was just taken by someone else. Please pick another.")
            if 'unique_patient_day' in str(e):
                return Result.fail("Patient already has an active booking on this date.")
            return Result.fail(f"Booking failed: {e}")

    def confirm(self, appt_id: int, user_id: int = None) -> Result:
        try:
            self.repo.update_status(appt_id, 'confirmed')
            self.audit.log(user_id, 'UPDATE', 'appointments', appt_id, "Confirmed")
            return Result.ok(message="Appointment confirmed")
        except Exception as e:
            return Result.fail(f"Could not confirm: {e}")

    def complete(self, appt_id: int, user_id: int = None) -> Result:
        try:
            self.repo.update_status(appt_id, 'completed')
            self.audit.log(user_id, 'UPDATE', 'appointments', appt_id, "Completed")
            return Result.ok(message="Appointment marked as completed")
        except Exception as e:
            return Result.fail(f"Could not complete: {e}")

    def cancel(self, appt_id: int, notes: str = None, user_id: int = None) -> Result:
        try:
            self.repo.update_status(appt_id, 'cancelled', notes)
            self.audit.log(user_id, 'UPDATE', 'appointments', appt_id,
                           f"Cancelled. Reason: {notes}")
            return Result.ok(message="Appointment cancelled")
        except Exception as e:
            return Result.fail(f"Could not cancel: {e}")

    def get_by_date(self, target_date: date) -> Result:
        try:
            appointments = self.repo.get_by_date(target_date)
            return Result.ok(data=appointments)
        except Exception as e:
            return Result.fail(f"Could not load appointments: {e}")

    def get_by_patient(self, patient_id: int) -> Result:
        try:
            appointments = self.repo.get_by_patient(patient_id)
            return Result.ok(data=appointments)
        except Exception as e:
            return Result.fail(f"Could not load appointments: {e}")

    def get_pending_form_requests(self) -> Result:
        try:
            requests = self.repo.get_pending_form_requests()
            return Result.ok(data=requests)
        except Exception as e:
            return Result.fail(f"Could not load form requests: {e}")

    def block_slot(self, block_date: date, start_time: time,
                   end_time: time, reason: str, user_id: int = None) -> Result:
        try:
            b = BlockedSlot(id=None, block_date=block_date,
                            start_time=start_time, end_time=end_time, reason=reason)
            self.repo.add_blocked_slot(b)
            self.audit.log(user_id, 'CREATE', 'blocked_slots', None,
                           f"Blocked {block_date} {start_time}-{end_time}: {reason}")
            return Result.ok(message=f"Slots blocked from {start_time} to {end_time}")
        except Exception as e:
            return Result.fail(f"Could not block slot: {e}")
