from datetime import datetime
from models.models import Patient
from repositories.patient_repo import PatientRepository
from repositories.audit_repo import AuditRepository
from utils.result import Result


class PatientService:

    def __init__(self):
        self.repo = PatientRepository()
        self.audit = AuditRepository()

    def get_all(self) -> Result:
        try:
            patients = self.repo.get_all()
            return Result.ok(data=patients)
        except Exception as e:
            return Result.fail(f"Could not load patients: {e}")

    def get_by_id(self, patient_id: int) -> Result:
        try:
            patient = self.repo.get_by_id(patient_id)
            if not patient:
                return Result.fail("Patient not found")
            return Result.ok(data=patient)
        except Exception as e:
            return Result.fail(f"Error: {e}")

    def search(self, query: str) -> Result:
        try:
            patients = self.repo.search(query.strip())
            return Result.ok(data=patients)
        except Exception as e:
            return Result.fail(f"Search failed: {e}")

    def create(self, data: dict, user_id: int = None) -> Result:
        # Validation
        if not data.get('full_name', '').strip():
            return Result.fail("Patient name is required")
        if not data.get('phone', '').strip():
            return Result.fail("Phone number is required")
        if self.repo.phone_exists(data['phone']):
            return Result.fail("A patient with this phone number already exists")

        try:
            patient = Patient(
                id=None,
                full_name=data['full_name'].strip(),
                phone=data['phone'].strip(),
                dob=data.get('dob'),
                gender=data.get('gender'),
                email=data.get('email', '').strip() or None,
                address=data.get('address', '').strip() or None,
                blood_type=data.get('blood_type') or None,
                allergies=data.get('allergies', '').strip() or None,
                chronic_conditions=data.get('chronic_conditions', '').strip() or None,
                emergency_contact_name=data.get('emergency_contact_name', '').strip() or None,
                emergency_contact_phone=data.get('emergency_contact_phone', '').strip() or None,
                insurance_provider=data.get('insurance_provider', '').strip() or None,
                insurance_id=data.get('insurance_id', '').strip() or None,
                consent_given_at=datetime.now() if data.get('consent_given') else None,
            )
            created = self.repo.create(patient)
            self.audit.log(user_id, 'CREATE', 'patients', created.id,
                           f"New patient: {created.full_name}")
            return Result.ok(data=created, message=f"Patient '{created.full_name}' added successfully")
        except Exception as e:
            return Result.fail(f"Could not create patient: {e}")

    def update(self, patient_id: int, data: dict, user_id: int = None) -> Result:
        if not data.get('full_name', '').strip():
            return Result.fail("Patient name is required")
        if not data.get('phone', '').strip():
            return Result.fail("Phone number is required")
        if self.repo.phone_exists(data['phone'], exclude_id=patient_id):
            return Result.fail("Another patient already has this phone number")

        try:
            existing = self.repo.get_by_id(patient_id)
            if not existing:
                return Result.fail("Patient not found")

            existing.full_name = data['full_name'].strip()
            existing.phone = data['phone'].strip()
            existing.dob = data.get('dob', existing.dob)
            existing.gender = data.get('gender', existing.gender)
            existing.email = data.get('email', '').strip() or None
            existing.address = data.get('address', '').strip() or None
            existing.blood_type = data.get('blood_type') or None
            existing.allergies = data.get('allergies', '').strip() or None
            existing.chronic_conditions = data.get('chronic_conditions', '').strip() or None
            existing.emergency_contact_name = data.get('emergency_contact_name', '').strip() or None
            existing.emergency_contact_phone = data.get('emergency_contact_phone', '').strip() or None
            existing.insurance_provider = data.get('insurance_provider', '').strip() or None
            existing.insurance_id = data.get('insurance_id', '').strip() or None

            updated = self.repo.update(existing)
            self.audit.log(user_id, 'UPDATE', 'patients', patient_id,
                           f"Updated: {updated.full_name}")
            return Result.ok(data=updated, message="Patient updated successfully")
        except Exception as e:
            return Result.fail(f"Could not update patient: {e}")

    def delete(self, patient_id: int, user_id: int = None) -> Result:
        try:
            patient = self.repo.get_by_id(patient_id)
            if not patient:
                return Result.fail("Patient not found")
            self.repo.delete(patient_id)
            self.audit.log(user_id, 'DELETE', 'patients', patient_id,
                           f"Deleted: {patient.full_name}")
            return Result.ok(message=f"Patient '{patient.full_name}' deleted")
        except Exception as e:
            return Result.fail(f"Could not delete patient: {e}")
