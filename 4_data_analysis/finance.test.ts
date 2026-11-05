import test from 'node:test';
import assert from 'node:assert/strict';
import {
  calculateSavingsRate,
  calculateBudgetStatus,
  calculateFinancialSummary,
  calculateCategoryAnalysis,
  calculateMonthlyAnalysis,
  calculateStatisticalAnalysis,
  calculateSavingsGoalProjection,
  type Category,
  type Transaction,
  type SavingsGoal,
} from './finance';

test('calculateSavingsRate computes correct percentage and guards zero income', () => {
  assert.equal(calculateSavingsRate(1000, 400), 60);
  assert.equal(calculateSavingsRate(500, 500), 0);
  assert.equal(calculateSavingsRate(100, 150), -50);
  assert.equal(calculateSavingsRate(0, 100), 0);
  assert.equal(calculateSavingsRate(-50, 100), 0);
});

test('calculateBudgetStatus accurately detects overrun and remaining amount', () => {
  // Under budget
  const under = calculateBudgetStatus(5000, 3200);
  assert.equal(under.remaining_budget, 1800);
  assert.equal(under.utilization_rate, 64);
  assert.equal(under.is_overrun, false);
  assert.equal(under.overrun_amount, 0);

  // Over budget
  const over = calculateBudgetStatus(4000, 4800);
  assert.equal(over.remaining_budget, -800);
  assert.equal(over.utilization_rate, 120);
  assert.equal(over.is_overrun, true);
  assert.equal(over.overrun_amount, 800);

  // Exactly on budget
  const exact = calculateBudgetStatus(2500, 2500);
  assert.equal(exact.remaining_budget, 0);
  assert.equal(exact.utilization_rate, 100);
  assert.equal(exact.is_overrun, false);
});

test('calculateFinancialSummary computes income, expense, and net savings', () => {
  const transactions: Transaction[] = [
    { id: 1, type: 'Income', amount: 75000, transaction_date: '2026-01-01', category_id: 9, description: 'Salary' },
    { id: 2, type: 'Expense', amount: 15000, transaction_date: '2026-01-02', category_id: 2, description: 'Rent' },
    { id: 3, type: 'Expense', amount: 5000, transaction_date: '2026-01-05', category_id: 1, description: 'Groceries' },
  ];

  const summary = calculateFinancialSummary(transactions);
  assert.equal(summary.income, 75000);
  assert.equal(summary.expenses, 20000);
  assert.equal(summary.savings, 55000);
  assert.equal(summary.savings_rate, 73.33);
  assert.equal(summary.transaction_count, 3);
});

test('calculateCategoryAnalysis sorts by total and computes percentages', () => {
  const categories: Category[] = [
    { id: 1, name: 'Groceries', type: 'Expense', color: '#EF4444' },
    { id: 2, name: 'Rent', type: 'Expense', color: '#F59E0B' },
  ];

  const transactions: Transaction[] = [
    { id: 1, type: 'Expense', amount: 2000, transaction_date: '2026-01-02', category_id: 1, description: 'Store' },
    { id: 2, type: 'Expense', amount: 3000, transaction_date: '2026-01-05', category_id: 1, description: 'Supermarket' },
    { id: 3, type: 'Expense', amount: 5000, transaction_date: '2026-01-10', category_id: 2, description: 'Rent' },
  ];

  const result = calculateCategoryAnalysis(transactions, categories, 'Expense');
  assert.equal(result.length, 2);
  // Both have total 5000, each is 50%
  assert.equal(result[0].total, 5000);
  assert.equal(result[0].percentage, 50);
});

test('calculateStatisticalAnalysis computes mean, median, and std deviation', () => {
  const categories: Category[] = [
    { id: 1, name: 'Groceries', type: 'Expense', color: '#EF4444' },
    { id: 6, name: 'Entertainment', type: 'Expense', color: '#10B981' },
  ];

  const transactions: Transaction[] = [
    { id: 1, type: 'Expense', amount: 100, transaction_date: '2026-01-01', category_id: 1, description: 'A' },
    { id: 2, type: 'Expense', amount: 200, transaction_date: '2026-01-02', category_id: 1, description: 'B' },
    { id: 3, type: 'Expense', amount: 300, transaction_date: '2026-01-03', category_id: 6, description: 'C' },
  ];

  const stats = calculateStatisticalAnalysis(transactions, categories);
  assert.equal(stats.expense_count, 3);
  assert.equal(stats.expense_total, 600);
  assert.equal(stats.expense_mean, 200);
  assert.equal(stats.expense_median, 200);
  assert.equal(stats.max_expense, 300);
  assert.equal(stats.essential_total, 300); // 100 + 200 Groceries
  assert.equal(stats.discretionary_total, 300); // 300 Entertainment
});

test('calculateSavingsGoalProjection calculates progress and months', () => {
  const goal: SavingsGoal = {
    id: 1,
    name: 'Emergency Fund',
    target_amount: 100000,
    current_amount: 40000,
  };

  const projection = calculateSavingsGoalProjection(goal, 20000);
  assert.equal(projection.remaining_amount, 60000);
  assert.equal(projection.progress_percentage, 40);
  assert.equal(projection.estimated_months, 3);
  assert.equal(projection.is_completed, false);
});
