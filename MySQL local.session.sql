CREATE DATABASE IF NOT EXISTS mydb;
USE mydb;
CREATE TABLE IF NOT EXISTS mobile_numbers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    number VARCHAR(10) NOT NULL UNIQUE
);
INSERT INTO mobile_numbers (number)
VALUES ('9876543210'),
    ('9123456789');
SELECT *
FROM mobile_numbers;
DESCRIBE mobile_numbers;
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(15) UNIQUE NOT NULL,
    password VARCHAR(15) NOT NULL,
    role VARCHAR(15) DEFAULT 'user' -- 'admin' or 'user'
);