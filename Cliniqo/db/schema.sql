-- ============================================================
-- CLINIC MANAGEMENT SYSTEM - DATABASE SCHEMA
-- ============================================================

-- Staff / Users
CREATE TABLE IF NOT EXISTS users (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    email       VARCHAR(100) UNIQUE NOT NULL,
    password    VARCHAR(255) NOT NULL,           -- hashed (bcrypt)
    role        VARCHAR(20) NOT NULL             -- 'doctor', 'nurse', 'receptionist'
                CHECK (role IN ('doctor','nurse','receptionist')),
    is_active   BOOLEAN DEFAULT TRUE,
    created_at  TIMESTAMP DEFAULT NOW()
);

-- Patients
CREATE TABLE IF NOT EXISTS patients (
    id                        SERIAL PRIMARY KEY,
    full_name                 VARCHAR(150) NOT NULL,
    dob                       DATE,
    gender                    VARCHAR(10) CHECK (gender IN ('male','female','other')),
    phone                     VARCHAR(15) UNIQUE NOT NULL,
    email                     VARCHAR(100),
    address                   TEXT,
    blood_type                VARCHAR(5),
    allergies                 TEXT,
    chronic_conditions        TEXT,
    emergency_contact_name    VARCHAR(100),
    emergency_contact_phone   VARCHAR(15),
    insurance_provider        VARCHAR(100),
    insurance_id              VARCHAR(100),
    consent_given_at          TIMESTAMP,
    created_at                TIMESTAMP DEFAULT NOW(),
    updated_at                TIMESTAMP DEFAULT NOW()
);

-- Consultations (each visit)
CREATE TABLE IF NOT EXISTS consultations (
    id                SERIAL PRIMARY KEY,
    patient_id        INT NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    doctor_id         INT NOT NULL REFERENCES users(id),
    visit_date        DATE NOT NULL DEFAULT CURRENT_DATE,
    chief_complaint   TEXT,
    clinical_notes    TEXT,
    diagnosis         TEXT,
    tests_ordered     TEXT,
    follow_up_date    DATE,
    created_at        TIMESTAMP DEFAULT NOW()
);

-- Prescriptions (linked to a consultation)
CREATE TABLE IF NOT EXISTS prescriptions (
    id                  SERIAL PRIMARY KEY,
    consultation_id     INT NOT NULL REFERENCES consultations(id) ON DELETE CASCADE,
    patient_id          INT NOT NULL REFERENCES patients(id),
    medication_name     VARCHAR(150) NOT NULL,
    dosage              VARCHAR(100),
    frequency           VARCHAR(100),
    duration_days       INT,
    instructions        TEXT,
    refills_allowed     INT DEFAULT 0,
    created_at          TIMESTAMP DEFAULT NOW()
);

-- Clinic Configuration
CREATE TABLE IF NOT EXISTS clinic_config (
    id                  SERIAL PRIMARY KEY,
    slot_duration_mins  INT DEFAULT 10,
    morning_start       TIME DEFAULT '09:00',
    morning_end         TIME DEFAULT '13:00',
    evening_start       TIME DEFAULT '14:00',
    evening_end         TIME DEFAULT '18:00',
    working_days        INT[] DEFAULT '{1,2,3,4,5,6}',  -- 0=Sun, 6=Sat
    updated_at          TIMESTAMP DEFAULT NOW()
);

-- Appointments
CREATE TABLE IF NOT EXISTS appointments (
    id                  SERIAL PRIMARY KEY,
    patient_id          INT NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    doctor_id           INT REFERENCES users(id),
    appointment_date    DATE NOT NULL,
    time_slot           TIME NOT NULL,
    reason              TEXT,
    status              VARCHAR(20) DEFAULT 'pending'
                        CHECK (status IN ('pending','confirmed','completed','cancelled')),
    requested_via       VARCHAR(20) DEFAULT 'manual'
                        CHECK (requested_via IN ('manual','google_form')),
    notes               TEXT,
    created_at          TIMESTAMP DEFAULT NOW(),
    updated_at          TIMESTAMP DEFAULT NOW()
);

-- Unique: only 1 active appointment per slot per day
CREATE UNIQUE INDEX IF NOT EXISTS unique_slot
ON appointments (appointment_date, time_slot)
WHERE status IN ('pending', 'confirmed');

-- Unique: only 1 active appointment per patient per day
CREATE UNIQUE INDEX IF NOT EXISTS unique_patient_day
ON appointments (patient_id, appointment_date)
WHERE status IN ('pending', 'confirmed');

-- Blocked Slots (lunch, meetings, holidays)
CREATE TABLE IF NOT EXISTS blocked_slots (
    id          SERIAL PRIMARY KEY,
    block_date  DATE NOT NULL,
    start_time  TIME NOT NULL,
    end_time    TIME NOT NULL,
    reason      VARCHAR(100) DEFAULT 'blocked',
    created_at  TIMESTAMP DEFAULT NOW()
);

-- Audit Logs
CREATE TABLE IF NOT EXISTS audit_logs (
    id          SERIAL PRIMARY KEY,
    user_id     INT REFERENCES users(id),
    action      VARCHAR(20) NOT NULL,           -- CREATE, READ, UPDATE, DELETE
    table_name  VARCHAR(50) NOT NULL,
    record_id   INT,
    details     TEXT,                           -- JSON string of changes
    ip_address  VARCHAR(50),
    created_at  TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- SEED DATA
-- ============================================================

-- Default clinic config
INSERT INTO clinic_config (slot_duration_mins, morning_start, morning_end, evening_start, evening_end)
VALUES (10, '09:00', '13:00', '14:00', '18:00')
ON CONFLICT DO NOTHING;

-- Default doctor account (password: admin123 — change immediately!)
INSERT INTO users (name, email, password, role)
VALUES ('Dr. Admin', 'admin@clinic.com', '$2b$12$KIXkljDummyHashForNowXXXXXXXXXXXXXXXXXXXXXX', 'doctor')
ON CONFLICT DO NOTHING;
