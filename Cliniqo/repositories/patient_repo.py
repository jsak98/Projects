from typing import List, Optional
from models.models import Patient
from db.connection import DBConn


class PatientRepository:

    def get_all(self) -> List[Patient]:
        with DBConn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, full_name, phone, dob, gender, email, address,
                           blood_type, allergies, chronic_conditions,
                           emergency_contact_name, emergency_contact_phone,
                           insurance_provider, insurance_id,
                           consent_given_at, telegram_chat_id,
                           created_at, updated_at
                    FROM patients ORDER BY full_name
                """)
                return [self._map(row) for row in cur.fetchall()]

    def get_by_id(self, patient_id: int) -> Optional[Patient]:
        with DBConn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, full_name, phone, dob, gender, email, address,
                           blood_type, allergies, chronic_conditions,
                           emergency_contact_name, emergency_contact_phone,
                           insurance_provider, insurance_id,
                           consent_given_at, telegram_chat_id,
                           created_at, updated_at
                    FROM patients WHERE id = %s
                """, (patient_id,))
                row = cur.fetchone()
                return self._map(row) if row else None

    def search(self, query: str) -> List[Patient]:
        with DBConn() as conn:
            with conn.cursor() as cur:
                like = f"%{query}%"
                cur.execute("""
                    SELECT id, full_name, phone, dob, gender, email, address,
                           blood_type, allergies, chronic_conditions,
                           emergency_contact_name, emergency_contact_phone,
                           insurance_provider, insurance_id,
                           consent_given_at, telegram_chat_id,
                           created_at, updated_at
                    FROM patients
                    WHERE full_name ILIKE %s OR phone ILIKE %s
                    ORDER BY full_name
                """, (like, like))
                return [self._map(row) for row in cur.fetchall()]

    def phone_exists(self, phone: str, exclude_id: Optional[int] = None) -> bool:
        with DBConn() as conn:
            with conn.cursor() as cur:
                if exclude_id:
                    cur.execute("SELECT 1 FROM patients WHERE phone = %s AND id != %s", (phone, exclude_id))
                else:
                    cur.execute("SELECT 1 FROM patients WHERE phone = %s", (phone,))
                return cur.fetchone() is not None

    def create(self, p: Patient) -> Patient:
        with DBConn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO patients (
                        full_name, phone, dob, gender, email, address,
                        blood_type, allergies, chronic_conditions,
                        emergency_contact_name, emergency_contact_phone,
                        insurance_provider, insurance_id, consent_given_at
                    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    RETURNING id, created_at, updated_at
                """, (
                    p.full_name, p.phone, p.dob, p.gender, p.email, p.address,
                    p.blood_type, p.allergies, p.chronic_conditions,
                    p.emergency_contact_name, p.emergency_contact_phone,
                    p.insurance_provider, p.insurance_id, p.consent_given_at
                ))
                row = cur.fetchone()
                p.id = row[0]
                p.created_at = row[1]
                p.updated_at = row[2]
                return p

    def update(self, p: Patient) -> Patient:
        with DBConn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE patients SET
                        full_name=%s, phone=%s, dob=%s, gender=%s, email=%s,
                        address=%s, blood_type=%s, allergies=%s,
                        chronic_conditions=%s, emergency_contact_name=%s,
                        emergency_contact_phone=%s, insurance_provider=%s,
                        insurance_id=%s, updated_at=NOW()
                    WHERE id=%s
                """, (
                    p.full_name, p.phone, p.dob, p.gender, p.email,
                    p.address, p.blood_type, p.allergies,
                    p.chronic_conditions, p.emergency_contact_name,
                    p.emergency_contact_phone, p.insurance_provider,
                    p.insurance_id, p.id
                ))
                return p

    def delete(self, patient_id: int):
        with DBConn() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM patients WHERE id = %s", (patient_id,))

    def _map(self, row) -> Patient:
        return Patient(
            id=row[0], full_name=row[1], phone=row[2], dob=row[3],
            gender=row[4], email=row[5], address=row[6], blood_type=row[7],
            allergies=row[8], chronic_conditions=row[9],
            emergency_contact_name=row[10], emergency_contact_phone=row[11],
            insurance_provider=row[12], insurance_id=row[13],
            consent_given_at=row[14], telegram_chat_id=row[15],
            created_at=row[16], updated_at=row[17]
        )
