/**
 * Core Financial Math & Data Analysis Engine for PennyWise
 * Pure deterministic functions for budgeting, variances, trends, and statistics.
 */

export interface Category {
  id: number;
  name: string;
  type: 'Income' | 'Expense';
  color: string;
}

export interface Transaction {
  id: number;
  type: 'Income' | 'Expense';
  amount: number;
  transaction_date: string; // YYYY-MM-DD
  category_id: number;
  description: string;
}

export interface Budget {
  id: number;
  category_id: number;
  month: string; // YYYY-MM
  amount: number;
}

export interface SavingsGoal {
  id: number;
  name: string;
  target_amount: number;
  current_amount: number;
}

export interface FinancialSummary {
  income: number;
  expenses: number;
  savings: number;
  savings_rate: number;
  transaction_count: number;
  average_transaction: number;
}

export interface BudgetStatusItem {
  id: number;
  category_id: number;
  category_name: string;
  category_color: string;
  month: string;
  budget_amount: number;
  actual_spending: number;
  remaining_budget: number;
  utilization_rate: number;
  is_overrun: boolean;
  overrun_amount: number;
}

export interface CategoryMetric {
  category_id: number;
  category_name: string;
  category_color: string;
  type: 'Income' | 'Expense';
  total: number;
  count: number;
  percentage: number;
}

export interface MonthlyMetric {
  month: string;
  income: number;
  expense: number;
  savings: number;
  savings_rate: number;
}

export interface StatisticalAnalysis {
  expense_count: number;
  expense_total: number;
  expense_mean: number;
  expense_median: number;
  expense_std_dev: number;
  max_expense: number;
  essential_total: number;
  discretionary_total: number;
  essential_ratio: number;
  discretionary_ratio: number;
}

/**
 * Calculates net savings and handles division by zero for savings rate
 */
export function calculateSavingsRate(income: number, expenses: number): number {
  if (income <= 0) return 0;
  const net = income - expenses;
  return Number(((net / income) * 100).toFixed(2));
}

/**
 * Calculates budget status for a given allocated amount and spent amount
 */
export function calculateBudgetStatus(budgetAmount: number, actualSpending: number) {
  const safeBudget = Number(budgetAmount) || 0;
  const safeActual = Number(actualSpending) || 0;
  const remaining = safeBudget - safeActual;
  const utilization = safeBudget > 0 ? (safeActual / safeBudget) * 100 : 0;
  const isOverrun = safeActual > safeBudget;
  const overrunAmount = isOverrun ? safeActual - safeBudget : 0;

  return {
    remaining_budget: Number(remaining.toFixed(2)),
    utilization_rate: Number(utilization.toFixed(2)),
    is_overrun: isOverrun,
    overrun_amount: Number(overrunAmount.toFixed(2)),
  };
}

/**
 * Computes overall financial summary for a set of transactions
 */
export function calculateFinancialSummary(transactions: Transaction[]): FinancialSummary {
  let income = 0;
  let expenses = 0;

  for (const t of transactions) {
    const amt = Number(t.amount) || 0;
    if (t.type.toLowerCase() === 'income') {
      income += amt;
    } else {
      expenses += amt;
    }
  }

  const savings = income - expenses;
  const savings_rate = calculateSavingsRate(income, expenses);
  const count = transactions.length;
  const average_transaction = count > 0 ? (income + expenses) / count : 0;

  return {
    income: Number(income.toFixed(2)),
    expenses: Number(expenses.toFixed(2)),
    savings: Number(savings.toFixed(2)),
    savings_rate,
    transaction_count: count,
    average_transaction: Number(average_transaction.toFixed(2)),
  };
}

/**
 * Aggregates transactions by category and calculates percentages
 */
export function calculateCategoryAnalysis(
  transactions: Transaction[],
  categories: Category[],
  typeFilter: 'Income' | 'Expense' = 'Expense'
): CategoryMetric[] {
  const catMap = new Map<number, Category>();
  categories.forEach((c) => catMap.set(c.id, c));

  const filtered = transactions.filter(
    (t) => t.type.toLowerCase() === typeFilter.toLowerCase()
  );
  const totalAmount = filtered.reduce((acc, t) => acc + (Number(t.amount) || 0), 0);

  const group = new Map<number, { total: number; count: number }>();
  for (const t of filtered) {
    const current = group.get(t.category_id) || { total: 0, count: 0 };
    group.set(t.category_id, {
      total: current.total + (Number(t.amount) || 0),
      count: current.count + 1,
    });
  }

  const results: CategoryMetric[] = [];
  for (const [catId, stats] of group.entries()) {
    const cat = catMap.get(catId);
    results.push({
      category_id: catId,
      category_name: cat ? cat.name : `Category #${catId}`,
      category_color: cat ? cat.color : '#94A3B8',
      type: typeFilter,
      total: Number(stats.total.toFixed(2)),
      count: stats.count,
      percentage:
        totalAmount > 0
          ? Number(((stats.total / totalAmount) * 100).toFixed(1))
          : 0,
    });
  }

  return results.sort((a, b) => b.total - a.total);
}

/**
 * Generates monthly metrics for transactions
 */
export function calculateMonthlyAnalysis(transactions: Transaction[]): MonthlyMetric[] {
  const monthsMap = new Map<string, { income: number; expense: number }>();

  for (const t of transactions) {
    const month = (t.transaction_date || '').slice(0, 7);
    if (!month || month.length !== 7) continue;

    const cur = monthsMap.get(month) || { income: 0, expense: 0 };
    const amt = Number(t.amount) || 0;
    if (t.type.toLowerCase() === 'income') {
      cur.income += amt;
    } else {
      cur.expense += amt;
    }
    monthsMap.set(month, cur);
  }

  const sortedMonths = Array.from(monthsMap.keys()).sort();
  return sortedMonths.map((m) => {
    const item = monthsMap.get(m)!;
    const savings = item.income - item.expense;
    return {
      month: m,
      income: Number(item.income.toFixed(2)),
      expense: Number(item.expense.toFixed(2)),
      savings: Number(savings.toFixed(2)),
      savings_rate: calculateSavingsRate(item.income, item.expense),
    };
  });
}

/**
 * Advanced Statistical Analysis (inspired by Data Analysis. py.py and Pandas analytics)
 */
export function calculateStatisticalAnalysis(
  transactions: Transaction[],
  categories: Category[]
): StatisticalAnalysis {
  const expenseTransactions = transactions
    .filter((t) => t.type.toLowerCase() === 'expense')
    .map((t) => ({ ...t, amount: Number(t.amount) || 0 }));

  if (expenseTransactions.length === 0) {
    return {
      expense_count: 0,
      expense_total: 0,
      expense_mean: 0,
      expense_median: 0,
      expense_std_dev: 0,
      max_expense: 0,
      essential_total: 0,
      discretionary_total: 0,
      essential_ratio: 0,
      discretionary_ratio: 0,
    };
  }

  const amounts = expenseTransactions.map((t) => t.amount).sort((a, b) => a - b);
  const total = amounts.reduce((a, b) => a + b, 0);
  const count = amounts.length;
  const mean = total / count;

  // Median
  const mid = Math.floor(count / 2);
  const median = count % 2 !== 0 ? amounts[mid] : (amounts[mid - 1] + amounts[mid]) / 2;

  // Standard deviation (sample std dev)
  const variance =
    count > 1
      ? amounts.reduce((acc, val) => acc + Math.pow(val - mean, 2), 0) / (count - 1)
      : 0;
  const stdDev = Math.sqrt(variance);

  // Essential vs Discretionary
  const catMap = new Map<number, string>();
  categories.forEach((c) => catMap.set(c.id, c.name.toLowerCase()));

  const essentialKeywords = [
    'groceries',
    'rent',
    'mortgage',
    'transportation',
    'fuel',
    'transit',
    'healthcare',
    'medical',
    'utilities',
    'electricity',
    'water',
    'education',
    'bills',
  ];

  let essentialTotal = 0;
  let discretionaryTotal = 0;

  for (const t of expenseTransactions) {
    const catName = (catMap.get(t.category_id) || '').toLowerCase();
    const isEssential = essentialKeywords.some((keyword) => catName.includes(keyword));
    if (isEssential) {
      essentialTotal += t.amount;
    } else {
      discretionaryTotal += t.amount;
    }
  }

  const essentialRatio = total > 0 ? (essentialTotal / total) * 100 : 0;
  const discretionaryRatio = total > 0 ? (discretionaryTotal / total) * 100 : 0;

  return {
    expense_count: count,
    expense_total: Number(total.toFixed(2)),
    expense_mean: Number(mean.toFixed(2)),
    expense_median: Number(median.toFixed(2)),
    expense_std_dev: Number(stdDev.toFixed(2)),
    max_expense: amounts[count - 1],
    essential_total: Number(essentialTotal.toFixed(2)),
    discretionary_total: Number(discretionaryTotal.toFixed(2)),
    essential_ratio: Number(essentialRatio.toFixed(1)),
    discretionary_ratio: Number(discretionaryRatio.toFixed(1)),
  };
}

/**
 * Calculates Savings Goals projection
 */
export function calculateSavingsGoalProjection(
  goal: SavingsGoal,
  averageMonthlySavings: number
) {
  const target = Number(goal.target_amount) || 0;
  const current = Number(goal.current_amount) || 0;
  const remaining = Math.max(0, target - current);
  const progress = target > 0 ? (current / target) * 100 : 0;

  let estimatedMonths: number | null = null;
  if (averageMonthlySavings > 0 && remaining > 0) {
    estimatedMonths = Math.ceil(remaining / averageMonthlySavings);
  } else if (remaining === 0) {
    estimatedMonths = 0;
  }

  return {
    remaining_amount: Number(remaining.toFixed(2)),
    progress_percentage: Math.min(100, Number(progress.toFixed(1))),
    is_completed: current >= target,
    estimated_months: estimatedMonths,
  };
}
