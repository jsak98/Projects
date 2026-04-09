from typing import List, Optional
from models.models import Consultation, Prescription
from db.connection import DBConn


class ConsultationRepository:

    def get_by_patient(self, patient_id: int) -> List[dict]:
        with DBConn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT c.id, c.visit_date, c.chief_complaint, c.clinical_notes,
                           c.diagnosis, c.tests_ordered, c.follow_up_date,
                           u.name as doctor_name
                    FROM consultations c
                    JOIN users u ON u.id = c.doctor_id
                    WHERE c.patient_id = %s
                    ORDER BY c.visit_date DESC
                """, (patient_id,))
                cols = ['id','visit_date','chief_complaint','clinical_notes',
                        'diagnosis','tests_ordered','follow_up_date','doctor_name']
                return [dict(zip(cols, row)) for row in cur.fetchall()]

    def get_by_id(self, consultation_id: int) -> Optional[dict]:
        with DBConn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT c.*, u.name as doctor_name, p.full_name as patient_name
                    FROM consultations c
                    JOIN users u ON u.id = c.doctor_id
                    JOIN patients p ON p.id = c.patient_id
                    WHERE c.id = %s
                """, (consultation_id,))
                row = cur.fetchone()
                if not row:
                    return None
                cols = ['id','patient_id','doctor_id','visit_date','chief_complaint',
                        'clinical_notes','diagnosis','tests_ordered','follow_up_date',
                        'created_at','doctor_name','patient_name']
                return dict(zip(cols, row))

    def create(self, c: Consultation) -> Consultation:
        with DBConn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO consultations
                        (patient_id, doctor_id, visit_date, chief_complaint,
                         clinical_notes, diagnosis, tests_ordered, follow_up_date)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                    RETURNING id, created_at
                """, (
                    c.patient_id, c.doctor_id, c.visit_date,
                    c.chief_complaint, c.clinical_notes, c.diagnosis,
                    c.tests_ordered, c.follow_up_date
                ))
                row = cur.fetchone()
                c.id = row[0]
                c.created_at = row[1]
                return c

    def update(self, c: Consultation) -> Consultation:
        with DBConn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE consultations SET
                        chief_complaint=%s, clinical_notes=%s,
                        diagnosis=%s, tests_ordered=%s, follow_up_date=%s
                    WHERE id=%s
                """, (
                    c.chief_complaint, c.clinical_notes,
                    c.diagnosis, c.tests_ordered,
                    c.follow_up_date, c.id
                ))
                return c

    def delete(self, consultation_id: int):
        with DBConn() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM consultations WHERE id = %s", (consultation_id,))


class PrescriptionRepository:

    def get_by_consultation(self, consultation_id: int) -> List[dict]:
        with DBConn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, medication_name, dosage, frequency,
                           duration_days, instructions, refills_allowed
                    FROM prescriptions WHERE consultation_id = %s
                """, (consultation_id,))
                cols = ['id','medication_name','dosage','frequency',
                        'duration_days','instructions','refills_allowed']
                return [dict(zip(cols, row)) for row in cur.fetchall()]

    def get_by_patient(self, patient_id: int) -> List[dict]:
        with DBConn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT p.id, p.medication_name, p.dosage, p.frequency,
                           p.duration_days, p.instructions, p.refills_allowed,
                           p.created_at, c.visit_date
                    FROM prescriptions p
                    JOIN consultations c ON c.id = p.consultation_id
                    WHERE p.patient_id = %s
                    ORDER BY p.created_at DESC
                """, (patient_id,))
                cols = ['id','medication_name','dosage','frequency','duration_days',
                        'instructions','refills_allowed','created_at','visit_date']
                return [dict(zip(cols, row)) for row in cur.fetchall()]

    def create(self, p: Prescription) -> Prescription:
        with DBConn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO prescriptions
                        (consultation_id, patient_id, medication_name, dosage,
                         frequency, duration_days, instructions, refills_allowed)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                    RETURNING id, created_at
                """, (
                    p.consultation_id, p.patient_id, p.medication_name,
                    p.dosage, p.frequency, p.duration_days,
                    p.instructions, p.refills_allowed
                ))
                row = cur.fetchone()
                p.id = row[0]
                p.created_at = row[1]
                return p

    def delete(self, prescription_id: int):
        with DBConn() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM prescriptions WHERE id = %s", (prescription_id,))
