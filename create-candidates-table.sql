CREATE TABLE candidates (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    email VARCHAR(200) NOT NULL,
    role VARCHAR(100),
    minio_path VARCHAR(500) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);