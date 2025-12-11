
-- Users Table (Employers and Job Seekers)
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    role VARCHAR(20) CHECK (role IN ('employer', 'job_seeker', 'admin')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Profiles for Job Seekers
CREATE TABLE profiles (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id),
    phone VARCHAR(15),
    skills TEXT[],
    experience_years INT,
    resume_url VARCHAR(255),
    vector_embedding VECTOR(1536) -- For AI matching
);

-- Employers Company Info
CREATE TABLE employers (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id),
    company_name VARCHAR(255),
    industry VARCHAR(100),
    location VARCHAR(100),
    verified BOOLEAN DEFAULT FALSE
);

-- Job Postings
CREATE TABLE jobs (
    id SERIAL PRIMARY KEY,
    employer_id INT REFERENCES employers(id),
    title VARCHAR(100) NOT NULL,
    description TEXT,
    location VARCHAR(100),
    salary_min INT,
    salary_max INT,
    type VARCHAR(50) CHECK (type IN ('Full-time', 'Part-time', 'Contract', 'Daily Wage')),
    status VARCHAR(20) DEFAULT 'Active' CHECK (status IN ('Active', 'Closed', 'Draft')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Job Applications
CREATE TABLE applications (
    id SERIAL PRIMARY KEY,
    job_id INT REFERENCES jobs(id),
    applicant_id INT REFERENCES profiles(id),
    status VARCHAR(20) DEFAULT 'Applied' CHECK (status IN ('Applied', 'Interviewing', 'Hired', 'Rejected')),
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT
);

-- Analytics / Events
CREATE TABLE events (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id),
    event_type VARCHAR(50),
    event_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
