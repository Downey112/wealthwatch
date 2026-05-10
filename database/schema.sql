-- WealthWatch Database Schema
-- Run this in Azure Data Studio connected to your database

-- Users table
CREATE TABLE users (
    user_id INT IDENTITY(1,1) PRIMARY KEY,
    email NVARCHAR(255) UNIQUE NOT NULL,
    display_name NVARCHAR(100),
    created_at DATETIME DEFAULT GETDATE()
);

-- Transactions table
CREATE TABLE transactions (
    transaction_id INT IDENTITY(1,1) PRIMARY KEY,
    user_id INT NOT NULL,
    amount DECIMAL(10,2) NOT NULL CHECK (amount > 0),
    type NVARCHAR(10) NOT NULL CHECK (type IN ('income', 'expense')),
    category NVARCHAR(50) NOT NULL,
    description NVARCHAR(255),
    transaction_date DATE NOT NULL,
    created_at DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Create indexes for performance
CREATE INDEX idx_user_date ON transactions(user_id, transaction_date);
CREATE INDEX idx_user_category ON transactions(user_id, category);

-- Sample categories
CREATE TABLE default_categories (
    category_id INT IDENTITY(1,1) PRIMARY KEY,
    name NVARCHAR(50) UNIQUE NOT NULL,
    type NVARCHAR(10) NOT NULL
);

INSERT INTO default_categories (name, type) VALUES
('Salary', 'income'),
('Freelance', 'income'),
('Food', 'expense'),
('Transport', 'expense'),
('Housing', 'expense'),
('Utilities', 'expense'),
('Entertainment', 'expense'),
('Healthcare', 'expense'),
('Shopping', 'expense'),
('Education', 'expense');

-- Stored Procedure: Monthly Summary
CREATE PROCEDURE GetMonthlySummary
    @user_id INT,
    @year INT,
    @month INT
AS
BEGIN
    SELECT 
        SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END) as total_income,
        SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END) as total_expense,
        SUM(CASE WHEN type = 'income' THEN amount ELSE -amount END) as net_savings
    FROM transactions
    WHERE user_id = @user_id 
        AND YEAR(transaction_date) = @year 
        AND MONTH(transaction_date) = @month;
END;

-- Stored Procedure: Category Breakdown
CREATE PROCEDURE GetCategoryBreakdown
    @user_id INT,
    @year INT,
    @month INT
AS
BEGIN
    SELECT 
        category,
        SUM(amount) as total
    FROM transactions
    WHERE user_id = @user_id 
        AND type = 'expense'
        AND YEAR(transaction_date) = @year 
        AND MONTH(transaction_date) = @month
    GROUP BY category
    ORDER BY total DESC;
END;