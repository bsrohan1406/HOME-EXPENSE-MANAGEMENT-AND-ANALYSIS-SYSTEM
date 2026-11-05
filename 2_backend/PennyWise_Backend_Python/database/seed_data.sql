-- ============================================================================
-- Project Name: PennyWise – Home Budget Management and Expense Analysis System
-- File: seed_data.sql
-- Description: Demonstration seed data for testing and analysis modules
-- ============================================================================

USE pennywise;

-- Disable foreign key checks temporarily for clean insertion
SET FOREIGN_KEY_CHECKS = 0;

TRUNCATE TABLE transactions;
TRUNCATE TABLE budgets;
TRUNCATE TABLE categories;
TRUNCATE TABLE savings_goals;

SET FOREIGN_KEY_CHECKS = 1;

-- ----------------------------------------------------------------------------
-- Default Categories (Demonstration Data)
-- ----------------------------------------------------------------------------
INSERT INTO categories (id, name, kind, color) VALUES
-- Expense Categories
(1, 'Groceries', 'expense', '#EF4444'),
(2, 'Rent', 'expense', '#F59E0B'),
(3, 'Transportation', 'expense', '#3B82F6'),
(4, 'Healthcare', 'expense', '#EC4899'),
(5, 'Education', 'expense', '#8B5CF6'),
(6, 'Entertainment', 'expense', '#10B981'),
(7, 'Utilities', 'expense', '#6366F1'),
(8, 'Shopping', 'expense', '#14B8A6'),
-- Income Categories
(9, 'Salary', 'income', '#059669'),
(10, 'Freelance', 'income', '#0D9488'),
(11, 'Other Income', 'income', '#0284C7');

-- ----------------------------------------------------------------------------
-- Sample Transactions (Demonstration Data)
-- ----------------------------------------------------------------------------
INSERT INTO transactions (kind, amount, transaction_date, category_id, description) VALUES
-- January 2026 Records
('income', 75000.00, '2026-01-01', 9, 'Monthly Software Engineer Salary'),
('income', 12500.00, '2026-01-14', 10, 'Freelance Web Design Project'),
('expense', 15000.00, '2026-01-02', 2, 'Monthly Apartment Rent'),
('expense', 5200.50, '2026-01-05', 1, 'Supermarket Monthly Groceries'),
('expense', 1800.00, '2026-01-08', 3, 'Fuel and Public Transit Pass'),
('expense', 2400.00, '2026-01-12', 7, 'Electricity and Water Bills'),
('expense', 1650.00, '2026-01-19', 6, 'Weekend Movie and Dinner'),
('expense', 3500.00, '2026-01-24', 4, 'Dental Checkup and Medicines'),
('expense', 4200.00, '2026-01-28', 8, 'Online Shopping - Electronics'),

-- February 2026 Records
('income', 75000.00, '2026-02-01', 9, 'Monthly Software Engineer Salary'),
('income', 18000.00, '2026-02-18', 10, 'Freelance App Consultation'),
('expense', 15000.00, '2026-02-02', 2, 'Monthly Apartment Rent'),
('expense', 4850.00, '2026-02-04', 1, 'Groceries and Fresh Produce'),
('expense', 1600.00, '2026-02-09', 3, 'Monthly Fuel Refill'),
('expense', 2650.00, '2026-02-13', 7, 'Utility Bills'),
('expense', 2200.00, '2026-02-17', 5, 'Python Advanced Certification Course'),
('expense', 3100.00, '2026-02-22', 8, 'Apparel and Clothing Shopping'),
('expense', 1200.00, '2026-02-26', 6, 'Concert Tickets');

-- ----------------------------------------------------------------------------
-- Sample Budgets (YYYY-MM Format, Demonstration Data)
-- ----------------------------------------------------------------------------
INSERT INTO budgets (month, category_id, amount) VALUES
('2026-01', 1, 6000.00),
('2026-01', 2, 15000.00),
('2026-01', 3, 2000.00),
('2026-01', 7, 2500.00),
('2026-01', 8, 4000.00),
('2026-02', 1, 5500.00),
('2026-02', 2, 15000.00),
('2026-02', 3, 2000.00),
('2026-02', 7, 2500.00),
('2026-02', 5, 2000.00);

-- ----------------------------------------------------------------------------
-- Sample Savings Goals (Demonstration Data)
-- ----------------------------------------------------------------------------
INSERT INTO savings_goals (name, target_amount, current_amount) VALUES
('Emergency Fund (6 Months)', 150000.00, 75000.00),
('New Laptop Upgrade', 90000.00, 45000.00),
('Summer Vacation Trip', 60000.00, 20000.00);