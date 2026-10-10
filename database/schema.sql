-- WealthWatch database schema for Azure SQL / SQL Server.
-- Run once against an empty database (Azure Data Studio, SSMS or sqlcmd).
-- Local development needs none of this: the API creates a SQLite file itself.

CREATE TABLE users (
    user_id INT IDENTITY(1,1) PRIMARY KEY,
    email NVARCHAR(255) UNIQUE NOT NULL,
    display_name NVARCHAR(100),
    created_at DATETIME DEFAULT GETDATE()
);

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

-- Every query filters on user_id and a transaction_date range.
CREATE INDEX idx_user_date ON transactions(user_id, transaction_date);
