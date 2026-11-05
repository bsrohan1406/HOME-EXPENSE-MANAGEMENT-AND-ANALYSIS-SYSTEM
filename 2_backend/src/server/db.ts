import fs from 'node:fs';
import path from 'node:path';
import {
  type Category,
  type Transaction,
  type Budget,
  type SavingsGoal,
  calculateBudgetStatus,
  calculateCategoryAnalysis,
  calculateFinancialSummary,
  calculateMonthlyAnalysis,
  calculateStatisticalAnalysis,
  calculateSavingsGoalProjection,
} from '../utils/finance';

const DATA_DIR = path.resolve(process.cwd(), 'data');
const DB_FILE = path.join(DATA_DIR, 'pennywise_db.json');

export interface DatabaseState {
  categories: Category[];
  transactions: Transaction[];
  budgets: Budget[];
  goals: SavingsGoal[];
  settings: {
    currency: string;
    profileName: string;
    profileEmail: string;
    budgetAlertThreshold: number;
  };
}

const DEFAULT_CATEGORIES: Category[] = [
  { id: 1, name: 'Groceries', type: 'Expense', color: '#EF4444' },
  { id: 2, name: 'Rent', type: 'Expense', color: '#F59E0B' },
  { id: 3, name: 'Transportation', type: 'Expense', color: '#3B82F6' },
  { id: 4, name: 'Healthcare', type: 'Expense', color: '#EC4899' },
  { id: 5, name: 'Education', type: 'Expense', color: '#8B5CF6' },
  { id: 6, name: 'Entertainment', type: 'Expense', color: '#10B981' },
  { id: 7, name: 'Utilities', type: 'Expense', color: '#6366F1' },
  { id: 8, name: 'Shopping', type: 'Expense', color: '#14B8A6' },
  { id: 9, name: 'Salary', type: 'Income', color: '#059669' },
  { id: 10, name: 'Freelance', type: 'Income', color: '#0D9488' },
  { id: 11, name: 'Other Income', type: 'Income', color: '#0284C7' },
];

function getSampleTransactions(): Transaction[] {
  const now = new Date();
  const currentYm = now.toISOString().slice(0, 7);
  const prevMonthDate = new Date(now.getFullYear(), now.getMonth() - 1, 1);
  const prevYm = prevMonthDate.toISOString().slice(0, 7);

  return [
    // Previous Month Records
    { id: 1, type: 'Income', amount: 75000, transaction_date: `${prevYm}-01`, category_id: 9, description: 'Monthly Software Engineer Salary' },
    { id: 2, type: 'Income', amount: 15000, transaction_date: `${prevYm}-15`, category_id: 10, description: 'Freelance UI Design' },
    { id: 3, type: 'Expense', amount: 18000, transaction_date: `${prevYm}-02`, category_id: 2, description: 'Monthly Apartment Rent' },
    { id: 4, type: 'Expense', amount: 5600, transaction_date: `${prevYm}-05`, category_id: 1, description: 'Supermarket Groceries' },
    { id: 5, type: 'Expense', amount: 1800, transaction_date: `${prevYm}-09`, category_id: 3, description: 'Fuel & Metro Recharge' },
    { id: 6, type: 'Expense', amount: 2400, transaction_date: `${prevYm}-12`, category_id: 7, description: 'High-speed Fiber & Electricity' },
    { id: 7, type: 'Expense', amount: 1650, transaction_date: `${prevYm}-18`, category_id: 6, description: 'Weekend Cinema & Dinner' },
    { id: 8, type: 'Expense', amount: 3200, transaction_date: `${prevYm}-22`, category_id: 8, description: 'New Running Shoes' },

    // Current Month Records
    { id: 9, type: 'Income', amount: 80000, transaction_date: `${currentYm}-01`, category_id: 9, description: 'Monthly Software Engineer Salary' },
    { id: 10, type: 'Income', amount: 12000, transaction_date: `${currentYm}-04`, category_id: 10, description: 'Client Code Review & Consulting' },
    { id: 11, type: 'Expense', amount: 18000, transaction_date: `${currentYm}-02`, category_id: 2, description: 'Apartment Rent' },
    { id: 12, type: 'Expense', amount: 4850, transaction_date: `${currentYm}-03`, category_id: 1, description: 'Organic Market & Groceries' },
    { id: 13, type: 'Expense', amount: 1600, transaction_date: `${currentYm}-06`, category_id: 3, description: 'Monthly Transit Pass' },
    { id: 14, type: 'Expense', amount: 2650, transaction_date: `${currentYm}-08`, category_id: 7, description: 'Electricity & Water Bill' },
    { id: 15, type: 'Expense', amount: 1200, transaction_date: `${currentYm}-10`, category_id: 6, description: 'Concert Ticket' },
    { id: 16, type: 'Expense', amount: 3500, transaction_date: `${currentYm}-12`, category_id: 4, description: 'Annual Health Checkup' },
    { id: 17, type: 'Expense', amount: 4200, transaction_date: `${currentYm}-15`, category_id: 8, description: 'Electronics & Audio Gear' },
  ];
}

function getSampleBudgets(): Budget[] {
  const now = new Date();
  const currentYm = now.toISOString().slice(0, 7);
  const prevMonthDate = new Date(now.getFullYear(), now.getMonth() - 1, 1);
  const prevYm = prevMonthDate.toISOString().slice(0, 7);

  return [
    { id: 1, category_id: 1, month: prevYm, amount: 6500 },
    { id: 2, category_id: 2, month: prevYm, amount: 18000 },
    { id: 3, category_id: 3, month: prevYm, amount: 2500 },
    { id: 4, category_id: 7, month: prevYm, amount: 3000 },
    { id: 5, category_id: 8, month: prevYm, amount: 4000 },

    { id: 6, category_id: 1, month: currentYm, amount: 6000 },
    { id: 7, category_id: 2, month: currentYm, amount: 18000 },
    { id: 8, category_id: 3, month: currentYm, amount: 2500 },
    { id: 9, category_id: 4, month: currentYm, amount: 4000 },
    { id: 10, category_id: 6, month: currentYm, amount: 2000 },
    { id: 11, category_id: 7, month: currentYm, amount: 3000 },
    { id: 12, category_id: 8, month: currentYm, amount: 3500 },
  ];
}

const DEFAULT_GOALS: SavingsGoal[] = [
  { id: 1, name: 'Emergency Fund (6 Months)', target_amount: 150000, current_amount: 85000 },
  { id: 2, name: 'New M4 MacBook Pro', target_amount: 120000, current_amount: 72000 },
  { id: 3, name: 'Summer Vacation Trip', target_amount: 60000, current_amount: 24500 },
];

class DatabaseStore {
  private state: DatabaseState;

  constructor() {
    this.state = this.load();
  }

  private load(): DatabaseState {
    try {
      if (!fs.existsSync(DATA_DIR)) {
        fs.mkdirSync(DATA_DIR, { recursive: true });
      }
      if (fs.existsSync(DB_FILE)) {
        const raw = fs.readFileSync(DB_FILE, 'utf-8');
        return JSON.parse(raw);
      }
    } catch (e) {
      console.warn('Could not read existing database, falling back to seed defaults:', e);
    }
    return this.getInitialState();
  }

  private persist() {
    try {
      if (!fs.existsSync(DATA_DIR)) {
        fs.mkdirSync(DATA_DIR, { recursive: true });
      }
      fs.writeFileSync(DB_FILE, JSON.stringify(this.state, null, 2), 'utf-8');
    } catch (err) {
      console.error('Failed to write database file:', err);
    }
  }

  public getInitialState(): DatabaseState {
    return {
      categories: [...DEFAULT_CATEGORIES],
      transactions: getSampleTransactions(),
      budgets: getSampleBudgets(),
      goals: [...DEFAULT_GOALS],
      settings: {
        currency: 'INR',
        profileName: 'Veera Reddy',
        profileEmail: 'veera.reddy@pennywise.finance',
        budgetAlertThreshold: 85,
      },
    };
  }

  public resetToDefault(): DatabaseState {
    this.state = this.getInitialState();
    this.persist();
    return this.state;
  }

  // --- CATEGORIES ---
  public getCategories(typeFilter?: string): Category[] {
    if (!typeFilter) return this.state.categories;
    const filter = typeFilter.toLowerCase();
    return this.state.categories.filter((c) => c.type.toLowerCase() === filter);
  }

  public getCategoryById(id: number): Category | undefined {
    return this.state.categories.find((c) => c.id === id);
  }

  public addCategory(name: string, type: 'Income' | 'Expense', color: string = '#10B981'): Category {
    const trimmed = name.trim();
    if (!trimmed) throw new Error('Category name cannot be empty');
    if (this.state.categories.some((c) => c.name.toLowerCase() === trimmed.toLowerCase())) {
      throw new Error(`Category "${trimmed}" already exists`);
    }
    const maxId = this.state.categories.reduce((max, c) => Math.max(max, c.id), 0);
    const newCat: Category = {
      id: maxId + 1,
      name: trimmed,
      type: type === 'Income' ? 'Income' : 'Expense',
      color: color || '#10B981',
    };
    this.state.categories.push(newCat);
    this.persist();
    return newCat;
  }

  public updateCategory(id: number, updates: Partial<Category>): Category {
    const index = this.state.categories.findIndex((c) => c.id === id);
    if (index === -1) throw new Error(`Category ${id} not found`);

    if (updates.name) {
      const trimmed = updates.name.trim();
      const existing = this.state.categories.find(
        (c) => c.id !== id && c.name.toLowerCase() === trimmed.toLowerCase()
      );
      if (existing) throw new Error(`Category "${trimmed}" already exists`);
      this.state.categories[index].name = trimmed;
    }
    if (updates.type) {
      this.state.categories[index].type = updates.type;
    }
    if (updates.color) {
      this.state.categories[index].color = updates.color;
    }

    this.persist();
    return this.state.categories[index];
  }

  public deleteCategory(id: number): boolean {
    const inUse = this.state.transactions.some((t) => t.category_id === id);
    if (inUse) {
      throw new Error('Cannot delete category: it is used by existing transactions');
    }
    const beforeCount = this.state.categories.length;
    this.state.categories = this.state.categories.filter((c) => c.id !== id);
    // Also remove budgets for this category
    this.state.budgets = this.state.budgets.filter((b) => b.category_id !== id);
    this.persist();
    return this.state.categories.length < beforeCount;
  }

  // --- TRANSACTIONS ---
  public getTransactions(params?: {
    month?: string;
    year?: string;
    type?: string;
    category_id?: number;
    search?: string;
  }): Transaction[] {
    let list = [...this.state.transactions];

    if (params?.month) {
      const targetMonth = params.month; // e.g. "2026-02" or single digit
      list = list.filter((t) => {
        if (targetMonth.includes('-')) {
          return t.transaction_date.startsWith(targetMonth);
        }
        const m = parseInt(t.transaction_date.split('-')[1], 10);
        return m === parseInt(targetMonth, 10);
      });
    }

    if (params?.year) {
      list = list.filter((t) => t.transaction_date.startsWith(params.year!));
    }

    if (params?.type) {
      const typeFilter = params.type.toLowerCase();
      list = list.filter((t) => t.type.toLowerCase() === typeFilter);
    }

    if (params?.category_id) {
      const catId = Number(params.category_id);
      list = list.filter((t) => t.category_id === catId);
    }

    if (params?.search) {
      const q = params.search.toLowerCase().trim();
      const catMap = new Map<number, string>();
      this.state.categories.forEach((c) => catMap.set(c.id, c.name.toLowerCase()));

      list = list.filter((t) => {
        const descMatch = (t.description || '').toLowerCase().includes(q);
        const catName = catMap.get(t.category_id) || '';
        const catMatch = catName.includes(q);
        const amountMatch = t.amount.toString().includes(q);
        return descMatch || catMatch || amountMatch;
      });
    }

    // Sort by transaction_date DESC, then id DESC
    return list.sort((a, b) => {
      const dateCmp = b.transaction_date.localeCompare(a.transaction_date);
      return dateCmp !== 0 ? dateCmp : b.id - a.id;
    });
  }

  public getTransactionById(id: number): Transaction | undefined {
    return this.state.transactions.find((t) => t.id === id);
  }

  public addTransaction(data: {
    type: 'Income' | 'Expense';
    amount: number;
    transaction_date: string;
    category_id: number;
    description?: string;
  }): Transaction {
    const amount = Number(data.amount);
    if (!amount || amount <= 0) {
      throw new Error('Transaction amount must be greater than zero');
    }
    if (!data.transaction_date || !/^\d{4}-\d{2}-\d{2}$/.test(data.transaction_date)) {
      throw new Error('Transaction date must be in YYYY-MM-DD format');
    }
    const cat = this.getCategoryById(Number(data.category_id));
    if (!cat) {
      throw new Error(`Category with ID ${data.category_id} does not exist`);
    }

    const maxId = this.state.transactions.reduce((max, t) => Math.max(max, t.id), 0);
    const newTx: Transaction = {
      id: maxId + 1,
      type: data.type.toLowerCase() === 'income' ? 'Income' : 'Expense',
      amount: Number(amount.toFixed(2)),
      transaction_date: data.transaction_date,
      category_id: Number(data.category_id),
      description: (data.description || '').trim(),
    };

    this.state.transactions.push(newTx);
    this.persist();
    return newTx;
  }

  public updateTransaction(id: number, data: Partial<Transaction>): Transaction {
    const index = this.state.transactions.findIndex((t) => t.id === id);
    if (index === -1) throw new Error(`Transaction ${id} not found`);

    if (data.amount !== undefined) {
      const amt = Number(data.amount);
      if (amt <= 0) throw new Error('Transaction amount must be greater than zero');
      this.state.transactions[index].amount = Number(amt.toFixed(2));
    }
    if (data.type) {
      this.state.transactions[index].type =
        data.type.toLowerCase() === 'income' ? 'Income' : 'Expense';
    }
    if (data.transaction_date) {
      if (!/^\d{4}-\d{2}-\d{2}$/.test(data.transaction_date)) {
        throw new Error('Invalid date format');
      }
      this.state.transactions[index].transaction_date = data.transaction_date;
    }
    if (data.category_id !== undefined) {
      const cat = this.getCategoryById(Number(data.category_id));
      if (!cat) throw new Error(`Category ${data.category_id} does not exist`);
      this.state.transactions[index].category_id = Number(data.category_id);
    }
    if (data.description !== undefined) {
      this.state.transactions[index].description = data.description.trim();
    }

    this.persist();
    return this.state.transactions[index];
  }

  public deleteTransaction(id: number): boolean {
    const before = this.state.transactions.length;
    this.state.transactions = this.state.transactions.filter((t) => t.id !== id);
    this.persist();
    return this.state.transactions.length < before;
  }

  // --- BUDGETS ---
  public getBudgets(month?: string) {
    const targetMonth = month || new Date().toISOString().slice(0, 7);
    const list = this.state.budgets.filter((b) => b.month === targetMonth);
    const catMap = new Map<number, Category>();
    this.state.categories.forEach((c) => catMap.set(c.id, c));

    // Calculate actual spending in targetMonth for each category
    const expensesInMonth = this.state.transactions.filter(
      (t) => t.type.toLowerCase() === 'expense' && t.transaction_date.startsWith(targetMonth)
    );

    return list.map((b) => {
      const cat = catMap.get(b.category_id);
      const spent = expensesInMonth
        .filter((t) => t.category_id === b.category_id)
        .reduce((sum, t) => sum + t.amount, 0);

      const status = calculateBudgetStatus(b.amount, spent);
      return {
        id: b.id,
        category_id: b.category_id,
        category_name: cat ? cat.name : 'Unknown',
        category_color: cat ? cat.color : '#94A3B8',
        month: b.month,
        budget_amount: b.amount,
        actual_spending: Number(spent.toFixed(2)),
        ...status,
      };
    });
  }

  public addBudget(data: { category_id: number; month: string; amount: number }): Budget {
    const catId = Number(data.category_id);
    const cat = this.getCategoryById(catId);
    if (!cat) throw new Error(`Category ${catId} does not exist`);
    if (cat.type.toLowerCase() !== 'expense') {
      throw new Error(`Budgets can only be set for Expense categories. "${cat.name}" is an Income category.`);
    }

    const amount = Number(data.amount);
    if (amount <= 0) throw new Error('Budget amount must be positive');

    const month = (data.month || '').trim();
    if (!/^\d{4}-\d{2}$/.test(month)) {
      throw new Error('Month must be in YYYY-MM format');
    }

    const existing = this.state.budgets.find(
      (b) => b.category_id === catId && b.month === month
    );
    if (existing) {
      existing.amount = Number(amount.toFixed(2));
      this.persist();
      return existing;
    }

    const maxId = this.state.budgets.reduce((max, b) => Math.max(max, b.id), 0);
    const newBudget: Budget = {
      id: maxId + 1,
      category_id: catId,
      month,
      amount: Number(amount.toFixed(2)),
    };
    this.state.budgets.push(newBudget);
    this.persist();
    return newBudget;
  }

  public updateBudget(id: number, data: Partial<Budget>): Budget {
    const index = this.state.budgets.findIndex((b) => b.id === id);
    if (index === -1) throw new Error(`Budget ${id} not found`);

    if (data.amount !== undefined) {
      const amt = Number(data.amount);
      if (amt <= 0) throw new Error('Budget amount must be positive');
      this.state.budgets[index].amount = Number(amt.toFixed(2));
    }
    if (data.month) {
      if (!/^\d{4}-\d{2}$/.test(data.month)) throw new Error('Invalid month format');
      this.state.budgets[index].month = data.month;
    }
    if (data.category_id !== undefined) {
      this.state.budgets[index].category_id = Number(data.category_id);
    }

    this.persist();
    return this.state.budgets[index];
  }

  public deleteBudget(id: number): boolean {
    const before = this.state.budgets.length;
    this.state.budgets = this.state.budgets.filter((b) => b.id !== id);
    this.persist();
    return this.state.budgets.length < before;
  }

  // --- GOALS ---
  public getGoals() {
    // Calculate average monthly savings over last 3 months
    const monthly = calculateMonthlyAnalysis(this.state.transactions);
    const recentSavings = monthly.slice(-3).map((m) => Math.max(0, m.savings));
    const avgSavings =
      recentSavings.length > 0
        ? recentSavings.reduce((a, b) => a + b, 0) / recentSavings.length
        : 15000;

    return this.state.goals.map((g) => ({
      ...g,
      ...calculateSavingsGoalProjection(g, avgSavings),
    }));
  }

  public addGoal(data: { name: string; target_amount: number; current_amount?: number }): SavingsGoal {
    const name = (data.name || '').trim();
    if (!name) throw new Error('Goal name is required');
    const target = Number(data.target_amount);
    if (target <= 0) throw new Error('Target amount must be greater than zero');
    const current = Math.max(0, Number(data.current_amount || 0));

    const maxId = this.state.goals.reduce((max, g) => Math.max(max, g.id), 0);
    const newGoal: SavingsGoal = {
      id: maxId + 1,
      name,
      target_amount: Number(target.toFixed(2)),
      current_amount: Number(current.toFixed(2)),
    };
    this.state.goals.push(newGoal);
    this.persist();
    return newGoal;
  }

  public updateGoal(id: number, data: Partial<SavingsGoal>): SavingsGoal {
    const index = this.state.goals.findIndex((g) => g.id === id);
    if (index === -1) throw new Error(`Goal ${id} not found`);

    if (data.name !== undefined) {
      this.state.goals[index].name = data.name.trim();
    }
    if (data.target_amount !== undefined) {
      this.state.goals[index].target_amount = Number(data.target_amount);
    }
    if (data.current_amount !== undefined) {
      this.state.goals[index].current_amount = Number(data.current_amount);
    }

    this.persist();
    return this.state.goals[index];
  }

  public contributeToGoal(id: number, amount: number): SavingsGoal {
    const index = this.state.goals.findIndex((g) => g.id === id);
    if (index === -1) throw new Error(`Goal ${id} not found`);
    const amt = Number(amount);
    if (amt <= 0) throw new Error('Contribution amount must be greater than zero');

    this.state.goals[index].current_amount = Number(
      (this.state.goals[index].current_amount + amt).toFixed(2)
    );
    this.persist();
    return this.state.goals[index];
  }

  public deleteGoal(id: number): boolean {
    const before = this.state.goals.length;
    this.state.goals = this.state.goals.filter((g) => g.id !== id);
    this.persist();
    return this.state.goals.length < before;
  }

  // --- ANALYTICS ---
  public getSummary(month?: string) {
    let tx = this.state.transactions;
    if (month) {
      tx = tx.filter((t) => t.transaction_date.startsWith(month));
    }
    return calculateFinancialSummary(tx);
  }

  public getMonthlyAnalysis() {
    return calculateMonthlyAnalysis(this.state.transactions);
  }

  public getCategoryAnalysis(type: 'Income' | 'Expense' = 'Expense', month?: string) {
    let tx = this.state.transactions;
    if (month) {
      tx = tx.filter((t) => t.transaction_date.startsWith(month));
    }
    return calculateCategoryAnalysis(tx, this.state.categories, type);
  }

  public getStatisticalAnalysis(month?: string) {
    let tx = this.state.transactions;
    if (month) {
      tx = tx.filter((t) => t.transaction_date.startsWith(month));
    }
    return calculateStatisticalAnalysis(tx, this.state.categories);
  }

  // --- SETTINGS ---
  public getSettings() {
    return this.state.settings;
  }

  public updateSettings(updates: Partial<DatabaseState['settings']>) {
    this.state.settings = { ...this.state.settings, ...updates };
    this.persist();
    return this.state.settings;
  }
}

export const db = new DatabaseStore();
