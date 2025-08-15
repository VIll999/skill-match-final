-- Users table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- EMSI Skills table
CREATE TABLE IF NOT EXISTS emsi_skills (
    skill_id VARCHAR(50) PRIMARY KEY,
    skill_name VARCHAR(255) NOT NULL,
    skill_type VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User Skills table
CREATE TABLE IF NOT EXISTS user_skills_emsi (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    emsi_skill_id VARCHAR(50) NOT NULL,
    skill_name VARCHAR(255),
    skill_type VARCHAR(50),
    proficiency_level FLOAT DEFAULT 0.5,
    years_of_experience INT DEFAULT 0,
    last_used DATE,
    source VARCHAR(50),
    extraction_method VARCHAR(50),
    confidence FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (emsi_skill_id) REFERENCES emsi_skills(skill_id),
    UNIQUE KEY unique_user_skill (user_id, emsi_skill_id)
);

-- Job Postings table
CREATE TABLE IF NOT EXISTS job_postings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    external_id VARCHAR(255) UNIQUE,
    title VARCHAR(500) NOT NULL,
    company VARCHAR(255),
    location VARCHAR(255),
    description TEXT,
    salary_min DECIMAL(10, 2),
    salary_max DECIMAL(10, 2),
    category VARCHAR(100),
    experience_level VARCHAR(50),
    posted_date DATETIME,
    source VARCHAR(50),
    url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_category (category),
    INDEX idx_posted_date (posted_date)
);

-- Job Skills table
CREATE TABLE IF NOT EXISTS job_skills_emsi (
    id INT AUTO_INCREMENT PRIMARY KEY,
    job_id INT NOT NULL,
    emsi_skill_id VARCHAR(50) NOT NULL,
    skill_name VARCHAR(255),
    skill_type VARCHAR(50),
    importance_score FLOAT DEFAULT 1.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (job_id) REFERENCES job_postings(id) ON DELETE CASCADE,
    FOREIGN KEY (emsi_skill_id) REFERENCES emsi_skills(skill_id)
);

-- Resumes table
CREATE TABLE IF NOT EXISTS resumes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    filename VARCHAR(255),
    file_path VARCHAR(500),
    raw_text TEXT,
    parsed_content JSON,
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Alembic version table
CREATE TABLE IF NOT EXISTS alembic_version (
    version_num VARCHAR(32) NOT NULL,
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);