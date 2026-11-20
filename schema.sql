DROP DATABASE IF EXISTS job_tracker;
CREATE DATABASE job_tracker CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE job_tracker;

CREATE TABLE companies (
    company_id INT PRIMARY KEY AUTO_INCREMENT,
    company_name VARCHAR(100) NOT NULL,
    industry VARCHAR(50),
    website VARCHAR(200),
    city VARCHAR(50),
    state VARCHAR(50),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE jobs (
    job_id INT PRIMARY KEY AUTO_INCREMENT,
    company_id INT NOT NULL,
    job_title VARCHAR(100) NOT NULL,
    job_type ENUM('Full-time','Part-time','Contract','Internship') NOT NULL DEFAULT 'Full-time',
    salary_min INT,
    salary_max INT,
    job_url VARCHAR(300),
    date_posted DATE,
    requirements JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_jobs_company FOREIGN KEY (company_id)
        REFERENCES companies(company_id) ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT chk_salary_range CHECK (
        salary_min IS NULL OR salary_max IS NULL OR salary_max >= salary_min
    )
) ENGINE=InnoDB;

CREATE TABLE applications (
    application_id INT PRIMARY KEY AUTO_INCREMENT,
    job_id INT NOT NULL,
    application_date DATE NOT NULL,
    status ENUM('Applied','Screening','Interview','Offer','Rejected','Withdrawn') NOT NULL DEFAULT 'Applied',
    resume_version VARCHAR(50),
    cover_letter_sent BOOLEAN NOT NULL DEFAULT FALSE,
    interview_data JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_applications_job FOREIGN KEY (job_id)
        REFERENCES jobs(job_id) ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT uq_application_job UNIQUE (job_id)
) ENGINE=InnoDB;

CREATE TABLE contacts (
    contact_id INT PRIMARY KEY AUTO_INCREMENT,
    company_id INT NOT NULL,
    contact_name VARCHAR(100) NOT NULL,
    title VARCHAR(100),
    email VARCHAR(100),
    phone VARCHAR(20),
    linkedin_url VARCHAR(200),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_contacts_company FOREIGN KEY (company_id)
        REFERENCES companies(company_id) ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;

CREATE INDEX idx_jobs_company ON jobs(company_id);
CREATE INDEX idx_jobs_date_posted ON jobs(date_posted);
CREATE INDEX idx_applications_status ON applications(status);
CREATE INDEX idx_applications_date ON applications(application_date);
CREATE INDEX idx_contacts_company ON contacts(company_id);

INSERT INTO companies (company_name, industry, website, city, state, notes) VALUES
('TechCorp', 'Software', 'https://example.com/techcorp', 'Miami', 'FL', 'Growing product engineering team.'),
('DataCo', 'Analytics', 'https://example.com/dataco', 'Fort Lauderdale', 'FL', 'Hybrid analytics roles.');

INSERT INTO jobs (company_id, job_title, job_type, salary_min, salary_max, job_url, date_posted, requirements) VALUES
(1, 'Software Developer', 'Full-time', 70000, 95000, 'https://example.com/jobs/developer', CURRENT_DATE, JSON_ARRAY('Python','SQL','Flask')),
(2, 'Data Analyst', 'Full-time', 60000, 80000, 'https://example.com/jobs/analyst', CURRENT_DATE, JSON_ARRAY('Python','SQL','Tableau'));

INSERT INTO applications (job_id, application_date, status, resume_version, cover_letter_sent, interview_data) VALUES
(1, CURRENT_DATE, 'Applied', 'Software Resume v2', TRUE, JSON_OBJECT('interview_rounds', 0, 'next_steps', 'Await response'));

INSERT INTO contacts (company_id, contact_name, title, email, phone, linkedin_url, notes) VALUES
(1, 'Jordan Lee', 'Technical Recruiter', 'jordan.lee@example.com', '305-555-0142', 'https://www.linkedin.com', 'Met at campus career fair.');

