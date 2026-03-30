-- SQL file for database models
CREATE TABLE users (
    id INT PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE subscriptions (
    id INT PRIMARY KEY,
    user_id INT,
    billing_info TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Further database models...