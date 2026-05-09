-- WealthWatch Database Schema
-- Run this once after provisioning Azure SQL

-- Users table
CREATE TABLE users (
    id INT IDENTITY(1,1) PRIMARY KEY,
    github_username NVARCHAR(100) NOT NULL UNIQUE,
    display_name NVARCHAR(200),
    created_at DATETIME2 DEFAULT GETDATE()
);

-- Categories lookup table
CREATE TABLE categories (
    id INT IDENTITY(1,1) PRIMARY KEY,
    name NVARCHAR(50) NOT NULL UNIQUE
);

-- Seed default categories
INSERT INTO categories (name) VALUES
    ('Food & Drinks'),
    ('Transport'),
    ('Shopping'),
    ('Bills & Utilities'),
    ('Entertainment'),
    ('Healthcare'),
    ('Education'),
    ('Salary'),
    ('Freelance'),
    ('Other');

-- Transactions table
CREATE TABLE transactions (
    id INT IDENTITY(1,1) PRIMARY KEY,
    user_id INT NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    type NVARCHAR(10) NOT NULL CHECK (type IN ('income', 'expense')),
    category NVARCHAR(50) NOT NULL,
    note NVARCHAR(500),
    transaction_date DATE NOT NULL DEFAULT CAST(GETDATE() AS DATE),
    created_at DATETIME2 DEFAULT GETDATE(),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Index for fast user-based queries
CREATE INDEX idx_transactions_user_id ON transactions(user_id);
CREATE INDEX idx_transactions_date ON transactions(transaction_date);