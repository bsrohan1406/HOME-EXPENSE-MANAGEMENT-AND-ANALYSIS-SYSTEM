-- =====================================================================
-- PennyWise – Home Budget Management and Expense Analysis System
-- Expected Database Schema Contract
-- Database: MySQL 8.0+
-- =====================================================================

CREATE DATABASE IF NOT EXISTS pennywise_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE pennywise_db;

-- ---------------------------------------------------------------------
-- 1. Categories Table
-- Stores user-managed income and expense categories.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS categories (
    category_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    type ENUM('Income', 'Expense') NOT NULL,
    description VARCHAR(255) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_category_name_type UNIQUE (name, type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------
-- 2. Transactions Table
-- Stores all individual manual income and expense entries.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS transactions (
    transaction_id INT AUTO_INCREMENT PRIMARY KEY,
    transaction_date DATE NOT NULL,
    transaction_type ENUM('Income', 'Expense') NOT NULL,
    category_id INT NOT NULL,
    amount DECIMAL(12, 2) NOT NULL,
    description VARCHAR(255) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_transactions_category
        FOREIGN KEY (category_id) REFERENCES categories (category_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    CONSTRAINT chk_transaction_amount CHECK (amount > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------
-- 3. Monthly Budgets Table
-- Stores monthly budget allocations for expense categories.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS budgets (
    budget_id INT AUTO_INCREMENT PRIMARY KEY,
    category_id INT NOT NULL,
    month INT NOT NULL,
    year INT NOT NULL,
    budget_amount DECIMAL(12, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_budgets_category
        FOREIGN KEY (category_id) REFERENCES categories (category_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    CONSTRAINT uq_category_month_year UNIQUE (category_id, month, year),
    CONSTRAINT chk_budget_month CHECK (month >= 1 AND month <= 12),
    CONSTRAINT chk_budget_amount CHECK (budget_amount > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------
-- Indexes for optimized querying and analytics aggregation
-- ---------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions (transaction_date);
CREATE INDEX IF NOT EXISTS idx_transactions_type ON transactions (transaction_type);
CREATE INDEX IF NOT EXISTS idx_transactions_category ON transactions (category_id);
CREATE INDEX IF NOT EXISTS idx_budgets_period ON budgets (year, month);

-- ---------------------------------------------------------------------
-- Initial Seed Data: Standard Default Categories
-- ---------------------------------------------------------------------
INSERT IGNORE INTO categories (name, type, description) VALUES
('Groceries', 'Expense', 'Household food, groceries and daily provisions'),
('Rent', 'Expense', 'Monthly home rent or mortgage payment'),
('Transportation', 'Expense', 'Fuel, public transit, cab fares, and vehicle maintenance'),
('Healthcare', 'Expense', 'Doctor visits, medicines and health insurance'),
('Education', 'Expense', 'Tuition, courses, books and school fees'),
('Entertainment', 'Expense', 'Movies, outings, hobbies and events'),
('Utilities', 'Expense', 'Electricity, water, gas, and internet bills'),
('Shopping', 'Expense', 'Clothing, electronics, personal accessories'),
('Salary', 'Income', 'Monthly employment salary'),
('Business', 'Income', 'Income from business or commerce'),
('Freelancing', 'Income', 'Freelance projects and side contracts'),
('Investments', 'Income', 'Dividends, interest, capital gains'),
('Other Income', 'Income', 'Gifts, refunds, and miscellaneous income');
