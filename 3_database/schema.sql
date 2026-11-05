-- ============================================================================
-- Project Name: PennyWise – Home Budget Management and Expense Analysis System
-- File: schema.sql
-- Description: Complete MySQL database schema matching existing Flask-SQLAlchemy models
-- ============================================================================

-- Create Database
CREATE DATABASE IF NOT EXISTS pennywise CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE pennywise;

-- Drop existing tables in reverse order of foreign key dependencies to prevent errors
DROP TABLE IF EXISTS transactions;
DROP TABLE IF EXISTS budgets;
DROP TABLE IF EXISTS categories;
DROP TABLE IF EXISTS savings_goals;

-- ----------------------------------------------------------------------------
-- Table 1: categories
-- ----------------------------------------------------------------------------
CREATE TABLE categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(80) NOT NULL,
    kind ENUM('income', 'expense') NOT NULL,
    color VARCHAR(12) DEFAULT '#10B981',
    INDEX idx_categories_kind (kind)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------------------
-- Table 2: transactions
-- ----------------------------------------------------------------------------
CREATE TABLE transactions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    kind ENUM('income', 'expense') NOT NULL,
    amount DECIMAL(12,2) NOT NULL,
    transaction_date DATE NOT NULL,
    category_id INT NOT NULL,
    description VARCHAR(255),
    CONSTRAINT fk_transaction_category 
        FOREIGN KEY (category_id) 
        REFERENCES categories(id) 
        ON DELETE CASCADE 
        ON UPDATE CASCADE,
    INDEX idx_transactions_date (transaction_date),
    INDEX idx_transactions_category (category_id),
    INDEX idx_transactions_kind (kind)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------------------
-- Table 3: budgets
-- ----------------------------------------------------------------------------
CREATE TABLE budgets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    month VARCHAR(7) NOT NULL, -- Format: YYYY-MM
    category_id INT NOT NULL,
    amount DECIMAL(12,2) NOT NULL,
    CONSTRAINT fk_budget_category 
        FOREIGN KEY (category_id) 
        REFERENCES categories(id) 
        ON DELETE CASCADE 
        ON UPDATE CASCADE,
    CONSTRAINT uk_month_category UNIQUE KEY (month, category_id),
    INDEX idx_budgets_month (month)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------------------
-- Table 4: savings_goals
-- ----------------------------------------------------------------------------
CREATE TABLE savings_goals (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    target_amount DECIMAL(12,2) NOT NULL,
    current_amount DECIMAL(12,2) DEFAULT 0.00
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;