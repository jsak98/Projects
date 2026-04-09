from datetime import date
from models.models import Consultation, Prescription
from repositories.consultation_repo import ConsultationRepository, PrescriptionRepository
from repositories.audit_repo import AuditRepository
from utils.result import Result


class ConsultationService:

    def __init__(self):
        self.repo = ConsultationRepository()
        self.audit = AuditRepository()

    def get_by_patient(self, patient_id: int) -> Result:
        try:
            records = self.repo.get_by_patient(patient_id)
            return Result.ok(data=records)
        except Exception as e:
            return Result.fail(f"Could not load consultations: {e}")

    def get_by_id(self, consultation_id: int) -> Result:
        try:
            record = self.repo.get_by_id(consultation_id)
            if not record:
                return Result.fail("Consultation not found")
            return Result.ok(data=record)
        except Exception as e:
            return Result.fail(f"Error: {e}")

    def create(self, data: dict, user_id: int = None) -> Result:
        if not data.get('patient_id'):
            return Result.fail("Patient is required")
        if not data.get('doctor_id'):
            return Result.fail("Doctor is required")
        try:
            c = Consultation(
                id=None,
                patient_id=data['patient_id'],
                doctor_id=data['doctor_id'],
                visit_date=data.get('visit_date', date.today()),
                chief_complaint=data.get('chief_complaint', '').strip() or None,
                clinical_notes=data.get('clinical_notes', '').strip() or None,
                diagnosis=data.get('diagnosis', '').strip() or None,
                tests_ordered=data.get('tests_ordered', '').strip() or None,
                follow_up_date=data.get('follow_up_date'),
            )
            created = self.repo.create(c)
            self.audit.log(user_id, 'CREATE', 'consultations', created.id,
                           f"Consultation for patient {data['patient_id']}")
            return Result.ok(data=created, message="Consultation saved")
        except Exception as e:
            return Result.fail(f"Could not save consultation: {e}")

    def update(self, consultation_id: int, data: dict, user_id: int = None) -> Result:
        try:
            existing = self.repo.get_by_id(consultation_id)
            if not existing:
                return Result.fail("Consultation not found")
            c = Consultation(
                id=consultation_id,
                patient_id=existing['patient_id'],
                doctor_id=existing['doctor_id'],
                visit_date=existing['visit_date'],
                chief_complaint=data.get('chief_complaint', '').strip() or None,
                clinical_notes=data.get('clinical_notes', '').strip() or None,
                diagnosis=data.get('diagnosis', '').strip() or None,
                tests_ordered=data.get('tests_ordered', '').strip() or None,
                follow_up_date=data.get('follow_up_date'),
            )
            updated = self.repo.update(c)
            self.audit.log(user_id, 'UPDATE', 'consultations', consultation_id, "Updated")
            return Result.ok(data=updated, message="Consultation updated")
        except Exception as e:
            return Result.fail(f"Could not update: {e}")

    def delete(self, consultation_id: int, user_id: int = None) -> Result:
        try:
            self.repo.delete(consultation_id)
            self.audit.log(user_id, 'DELETE', 'consultations', consultation_id, "Deleted")
            return Result.ok(message="Consultation deleted")
        except Exception as e:
            return Result.fail(f"Could not delete: {e}")


class PrescriptionService:

    def __init__(self):
        self.repo = PrescriptionRepository()
        self.audit = AuditRepository()

    def get_by_consultation(self, consultation_id: int) -> Result:
        try:
            records = self.repo.get_by_consultation(consultation_id)
            return Result.ok(data=records)
        except Exception as e:
            return Result.fail(f"Could not load prescriptions: {e}")

    def get_by_patient(self, patient_id: int) -> Result:
        try:
            records = self.repo.get_by_patient(patient_id)
            return Result.ok(data=records)
        except Exception as e:
            return Result.fail(f"Could not load prescriptions: {e}")

    def create(self, data: dict, user_id: int = None) -> Result:
        if not data.get('medication_name', '').strip():
            return Result.fail("Medication name is required")
        try:
            p = Prescription(
                id=None,
                consultation_id=data['consultation_id'],
                patient_id=data['patient_id'],
                medication_name=data['medication_name'].strip(),
                dosage=data.get('dosage', '').strip() or None,
                frequency=data.get('frequency', '').strip() or None,
                duration_days=data.get('duration_days'),
                instructions=data.get('instructions', '').strip() or None,
                refills_allowed=data.get('refills_allowed', 0),
            )
            created = self.repo.create(p)
            self.audit.log(user_id, 'CREATE', 'prescriptions', created.id,
                           f"Prescribed: {created.medication_name}")
            return Result.ok(data=created, message=f"Prescription added: {created.medication_name}")
        except Exception as e:
            return Result.fail(f"Could not add prescription: {e}")

    def delete(self, prescription_id: int, user_id: int = None) -> Result:
        try:
            self.repo.delete(prescription_id)
            self.audit.log(user_id, 'DELETE', 'prescriptions', prescription_id, "Deleted")
            return Result.ok(message="Prescription removed")
        except Exception as e:
            return Result.fail(f"Could not delete: {e}")
