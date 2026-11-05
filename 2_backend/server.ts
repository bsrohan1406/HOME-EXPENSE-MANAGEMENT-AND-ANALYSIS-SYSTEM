import express, { Request, Response } from 'express';
import fs from 'node:fs';
import path from 'node:path';
import { db } from './src/server/db';

const app = express();
const args = process.argv.slice(2);
const portIndex = args.indexOf('--port');
const portArg = portIndex !== -1 && args[portIndex + 1] ? parseInt(args[portIndex + 1], 10) : null;
const PORT = portArg || (process.env.PORT ? parseInt(process.env.PORT, 10) : 3000);

app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Serve static assets from public/static and public
app.use('/static', express.static(path.resolve(process.cwd(), 'public', 'static')));
app.use(express.static(path.resolve(process.cwd(), 'public')));

// Template Rendering Engine for user frontend templates
function renderPage(pageName: string, title: string): string {
  const basePath = path.resolve(process.cwd(), 'templates', 'base.html');
  const childPath = path.resolve(process.cwd(), 'templates', `${pageName}.html`);

  const baseHtml = fs.readFileSync(basePath, 'utf-8');
  let childHtml = '';
  try {
    childHtml = fs.readFileSync(childPath, 'utf-8');
  } catch {
    childHtml = fs.readFileSync(path.resolve(process.cwd(), 'templates', '404.html'), 'utf-8');
  }

  // Extract block content
  const contentMatch = childHtml.match(/\{%\s*block\s+content\s*%\}([\s\S]*?)\{%\s*endblock\s*%\}/i);
  const content = contentMatch ? contentMatch[1] : childHtml;

  // Extract block scripts
  const scriptsMatch = childHtml.match(/\{%\s*block\s+scripts\s*%\}([\s\S]*?)\{%\s*endblock\s*%\}/i);
  const scripts = scriptsMatch ? scriptsMatch[1] : '';

  let output = baseHtml
    .replace(/\{\{\s*title\s*\}\}/g, title)
    .replace(/\{\{\s*url_for\('static',\s*filename='([^']+)'\)\s*\}\}/g, '/static/$1')
    .replace(/\{%\s*block\s+content\s*%\}([\s\S]*?)\{%\s*endblock\s*%\}/g, content)
    .replace(/\{%\s*block\s+scripts\s*%\}([\s\S]*?)\{%\s*endblock\s*%\}/g, scripts);

  // Replace {% if page == '...' %}active{% endif %}
  output = output.replace(/\{%\s*if\s+page\s*==\s*'([^']+)'\s*%\}\s*active\s*\{%\s*endif\s*%\}/g, (_, p) => {
    return p === pageName ? 'active' : '';
  });

  return output;
}

// Standard response builders matching backend docs
function successResponse(res: Response, data: any, message: string = 'Operation successful', statusCode: number = 200) {
  return res.status(statusCode).json({
    status: 'success',
    message,
    data,
  });
}

function errorResponse(res: Response, message: string, statusCode: number = 400) {
  return res.status(statusCode).json({
    status: 'error',
    message,
  });
}

// ----------------- SYSTEM ENDPOINTS -----------------
app.get('/api/health', (_req: Request, res: Response) => {
  res.json({
    service: 'PennyWise Backend API & Data Analysis System',
    status: 'healthy',
    timestamp: new Date().toISOString(),
    database: {
      type: 'Embedded Structured Store',
      connected: true,
      message: 'Database storage and connection pool is healthy',
    },
    modules: {
      transactions: 'active',
      categories: 'active',
      budgets: 'active',
      goals: 'active',
      analytics: 'active',
      data_analysis: 'active',
      charts: 'active',
    },
  });
});

app.post('/api/reset', (_req: Request, res: Response) => {
  const fresh = db.resetToDefault();
  return successResponse(res, fresh, 'Database successfully reset to demonstration seed data');
});

// ----------------- CATEGORY ENDPOINTS -----------------
app.get('/api/categories', (req: Request, res: Response) => {
  const typeFilter = req.query.type as string | undefined;
  const categories = db.getCategories(typeFilter);
  return successResponse(res, categories);
});

app.get('/api/categories/:id', (req: Request, res: Response) => {
  const id = parseInt(req.params.id, 10);
  const category = db.getCategoryById(id);
  if (!category) return errorResponse(res, `Category ${id} not found`, 404);
  return successResponse(res, category);
});

app.post('/api/categories', (req: Request, res: Response) => {
  try {
    const { name, type, color } = req.body;
    if (!name || !type) return errorResponse(res, 'Category name and type are required');
    const cat = db.addCategory(name, type, color);
    return successResponse(res, cat, 'Category created successfully', 201);
  } catch (err: any) {
    const isConflict = err.message && err.message.includes('already exists');
    return errorResponse(res, err.message, isConflict ? 409 : 400);
  }
});

app.put('/api/categories/:id', (req: Request, res: Response) => {
  try {
    const id = parseInt(req.params.id, 10);
    const updated = db.updateCategory(id, req.body);
    return successResponse(res, updated, 'Category updated successfully');
  } catch (err: any) {
    return errorResponse(res, err.message, 400);
  }
});

app.delete('/api/categories/:id', (req: Request, res: Response) => {
  try {
    const id = parseInt(req.params.id, 10);
    db.deleteCategory(id);
    return successResponse(res, { id }, 'Category deleted successfully');
  } catch (err: any) {
    const isConflict = err.message && err.message.includes('used by');
    return errorResponse(res, err.message, isConflict ? 409 : 400);
  }
});

// ----------------- TRANSACTION ENDPOINTS -----------------
app.get('/api/transactions', (req: Request, res: Response) => {
  const transactions = db.getTransactions({
    month: req.query.month as string | undefined,
    year: req.query.year as string | undefined,
    type: req.query.type as string | undefined,
    category_id: req.query.category_id ? parseInt(req.query.category_id as string, 10) : undefined,
    search: req.query.search as string | undefined,
  });
  return successResponse(res, transactions);
});

app.get('/api/transactions/:id', (req: Request, res: Response) => {
  const id = parseInt(req.params.id, 10);
  const tx = db.getTransactionById(id);
  if (!tx) return errorResponse(res, `Transaction ${id} not found`, 404);
  return successResponse(res, tx);
});

app.post('/api/transactions', (req: Request, res: Response) => {
  try {
    const { type, amount, transaction_date, category_id, description } = req.body;
    if (!type || !amount || !transaction_date || !category_id) {
      return errorResponse(res, 'Missing required fields: type, amount, transaction_date, category_id');
    }
    const tx = db.addTransaction({
      type,
      amount: parseFloat(amount),
      transaction_date,
      category_id: parseInt(category_id, 10),
      description,
    });
    return successResponse(res, tx, 'Transaction recorded successfully', 201);
  } catch (err: any) {
    return errorResponse(res, err.message, 400);
  }
});

app.put('/api/transactions/:id', (req: Request, res: Response) => {
  try {
    const id = parseInt(req.params.id, 10);
    const updated = db.updateTransaction(id, req.body);
    return successResponse(res, updated, 'Transaction updated successfully');
  } catch (err: any) {
    return errorResponse(res, err.message, 400);
  }
});

app.delete('/api/transactions/:id', (req: Request, res: Response) => {
  try {
    const id = parseInt(req.params.id, 10);
    db.deleteTransaction(id);
    return successResponse(res, { id }, 'Transaction deleted successfully');
  } catch (err: any) {
    return errorResponse(res, err.message, 400);
  }
});

// ----------------- BUDGET ENDPOINTS -----------------
app.get('/api/budgets', (req: Request, res: Response) => {
  const month = req.query.month as string | undefined;
  const budgets = db.getBudgets(month);
  return successResponse(res, budgets);
});

app.post('/api/budgets', (req: Request, res: Response) => {
  try {
    const { category_id, month, amount } = req.body;
    if (!category_id || !month || amount === undefined) {
      return errorResponse(res, 'category_id, month (YYYY-MM), and amount are required');
    }
    const budget = db.addBudget({
      category_id: parseInt(category_id, 10),
      month,
      amount: parseFloat(amount),
    });
    return successResponse(res, budget, 'Budget set successfully', 201);
  } catch (err: any) {
    return errorResponse(res, err.message, 400);
  }
});

app.put('/api/budgets/:id', (req: Request, res: Response) => {
  try {
    const id = parseInt(req.params.id, 10);
    const updated = db.updateBudget(id, req.body);
    return successResponse(res, updated, 'Budget updated successfully');
  } catch (err: any) {
    return errorResponse(res, err.message, 400);
  }
});

app.delete('/api/budgets/:id', (req: Request, res: Response) => {
  try {
    const id = parseInt(req.params.id, 10);
    db.deleteBudget(id);
    return successResponse(res, { id }, 'Budget deleted successfully');
  } catch (err: any) {
    return errorResponse(res, err.message, 400);
  }
});

// ----------------- SAVINGS GOALS ENDPOINTS -----------------
app.get('/api/goals', (_req: Request, res: Response) => {
  const goals = db.getGoals();
  return successResponse(res, goals);
});

app.post('/api/goals', (req: Request, res: Response) => {
  try {
    const { name, target_amount, current_amount } = req.body;
    const goal = db.addGoal({ name, target_amount, current_amount });
    return successResponse(res, goal, 'Savings goal created', 201);
  } catch (err: any) {
    return errorResponse(res, err.message, 400);
  }
});

app.put('/api/goals/:id', (req: Request, res: Response) => {
  try {
    const id = parseInt(req.params.id, 10);
    const updated = db.updateGoal(id, req.body);
    return successResponse(res, updated, 'Savings goal updated');
  } catch (err: any) {
    return errorResponse(res, err.message, 400);
  }
});

app.post('/api/goals/:id/contribute', (req: Request, res: Response) => {
  try {
    const id = parseInt(req.params.id, 10);
    const { amount } = req.body;
    const updated = db.contributeToGoal(id, parseFloat(amount));
    return successResponse(res, updated, 'Goal contribution recorded');
  } catch (err: any) {
    return errorResponse(res, err.message, 400);
  }
});

app.delete('/api/goals/:id', (req: Request, res: Response) => {
  try {
    const id = parseInt(req.params.id, 10);
    db.deleteGoal(id);
    return successResponse(res, { id }, 'Savings goal deleted');
  } catch (err: any) {
    return errorResponse(res, err.message, 400);
  }
});

// ----------------- ANALYTICS & DATA ANALYSIS -----------------
app.get('/api/analytics/summary', (req: Request, res: Response) => {
  const month = req.query.month as string | undefined;
  const summary = db.getSummary(month);
  return successResponse(res, summary);
});

app.get('/api/analytics/monthly', (_req: Request, res: Response) => {
  const monthly = db.getMonthlyAnalysis();
  return successResponse(res, monthly);
});

app.get('/api/analytics/categories', (req: Request, res: Response) => {
  const type = (req.query.type as 'Income' | 'Expense') || 'Expense';
  const month = req.query.month as string | undefined;
  const breakdown = db.getCategoryAnalysis(type, month);
  return successResponse(res, breakdown);
});

app.get('/api/analytics/budget-status', (req: Request, res: Response) => {
  const month = req.query.month as string | undefined;
  const budgets = db.getBudgets(month);
  return successResponse(res, budgets);
});

app.get('/api/analytics/savings', (_req: Request, res: Response) => {
  const goals = db.getGoals();
  return successResponse(res, goals);
});

app.get('/api/analytics/statistical', (req: Request, res: Response) => {
  const month = req.query.month as string | undefined;
  const stats = db.getStatisticalAnalysis(month);
  return successResponse(res, stats);
});

// ----------------- CHARTS (SVG Engine matching both /api/analytics/chart and /api/analytics/charts) -----------------
const handleChartRequest = (req: Request, res: Response) => {
  const { chartName } = req.params;
  const month = req.query.month as string | undefined;

  res.setHeader('Content-Type', 'image/svg+xml');

  if (chartName === 'expense-distribution' || chartName === 'categories') {
    const categories = db.getCategoryAnalysis('Expense', month);
    const total = categories.reduce((sum, c) => sum + c.total, 0);

    let startAngle = 0;
    const slices = categories.map((cat) => {
      const angle = total > 0 ? (cat.total / total) * 360 : 0;
      const slice = { ...cat, startAngle, angle };
      startAngle += angle;
      return slice;
    });

    const svg = `
      <svg xmlns="http://www.w3.org/2000/svg" width="600" height="400" viewBox="0 0 600 400" style="background:#0F172A; font-family:sans-serif;">
        <text x="300" y="35" text-anchor="middle" fill="#F8FAFC" font-size="18" font-weight="bold">Expense Distribution by Category</text>
        <g transform="translate(180, 210)">
          ${slices.length === 0 ? '<text x="0" y="0" text-anchor="middle" fill="#94A3B8">No expense data</text>' : ''}
          ${slices.map((s) => {
            const r = 110;
            const rInner = 60;
            const a1 = (s.startAngle - 90) * (Math.PI / 180);
            const a2 = (s.startAngle + s.angle - 90) * (Math.PI / 180);
            const x1 = r * Math.cos(a1);
            const y1 = r * Math.sin(a1);
            const x2 = r * Math.cos(a2);
            const y2 = r * Math.sin(a2);
            const xi1 = rInner * Math.cos(a1);
            const yi1 = rInner * Math.sin(a1);
            const xi2 = rInner * Math.cos(a2);
            const yi2 = rInner * Math.sin(a2);
            const large = s.angle > 180 ? 1 : 0;
            const pathData = `M ${xi1} ${yi1} L ${x1} ${y1} A ${r} ${r} 0 ${large} 1 ${x2} ${y2} L ${xi2} ${yi2} A ${rInner} ${rInner} 0 ${large} 0 ${xi1} ${yi1} Z`;
            return `<path d="${pathData}" fill="${s.category_color}" stroke="#0F172A" stroke-width="2"/>`;
          }).join('')}
          <text x="0" y="5" text-anchor="middle" fill="#F8FAFC" font-size="14" font-weight="bold">₹${total.toLocaleString()}</text>
        </g>
        <g transform="translate(360, 90)">
          ${categories.slice(0, 8).map((cat, i) => `
            <g transform="translate(0, ${i * 32})">
              <rect width="14" height="14" rx="3" fill="${cat.category_color}"/>
              <text x="22" y="12" fill="#E2E8F0" font-size="13">${cat.category_name}</text>
              <text x="190" y="12" fill="#94A3B8" font-size="13" text-anchor="end">${cat.percentage}%</text>
            </g>
          `).join('')}
        </g>
      </svg>
    `;
    return res.send(svg);
  }

  // Monthly comparison
  const monthly = db.getMonthlyAnalysis();
  const maxVal = Math.max(1000, ...monthly.map((m) => Math.max(m.income, m.expense)));
  const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" width="700" height="360" viewBox="0 0 700 360" style="background:#0F172A; font-family:sans-serif;">
      <text x="350" y="30" text-anchor="middle" fill="#F8FAFC" font-size="18" font-weight="bold">Monthly Income vs Expenses</text>
      <g transform="translate(70, 60)">
        <line x1="0" y1="240" x2="580" y2="240" stroke="#334155" stroke-width="2"/>
        ${monthly.slice(-6).map((m, i) => {
          const x = i * 95 + 20;
          const incHeight = (m.income / maxVal) * 220;
          const expHeight = (m.expense / maxVal) * 220;
          return `
            <rect x="${x}" y="${240 - incHeight}" width="28" height="${incHeight}" rx="4" fill="#10B981"/>
            <rect x="${x + 32}" y="${240 - expHeight}" width="28" height="${expHeight}" rx="4" fill="#EF4444"/>
            <text x="${x + 30}" y="260" text-anchor="middle" fill="#94A3B8" font-size="12">${m.month.slice(5)}</text>
          `;
        }).join('')}
      </g>
      <g transform="translate(500, 20)">
        <rect width="12" height="12" rx="3" fill="#10B981"/>
        <text x="18" y="11" fill="#E2E8F0" font-size="12">Income</text>
        <rect x="80" width="12" height="12" rx="3" fill="#EF4444"/>
        <text x="98" y="11" fill="#E2E8F0" font-size="12">Expense</text>
      </g>
    </svg>
  `;
  return res.send(svg);
};

app.get('/api/analytics/charts/:chartName', handleChartRequest);
app.get('/api/analytics/chart/:chartName', handleChartRequest);

// ----------------- CSV EXPORT -----------------
app.get('/api/export/csv', (_req: Request, res: Response) => {
  const transactions = db.getTransactions();
  const catMap = new Map<number, string>();
  db.getCategories().forEach((c) => catMap.set(c.id, c.name));

  const headers = ['ID', 'Date', 'Type', 'Category', 'Amount', 'Description'];
  const rows = transactions.map((t) => [
    t.id,
    t.transaction_date,
    t.type,
    `"${(catMap.get(t.category_id) || 'Uncategorized').replace(/"/g, '""')}"`,
    t.amount.toFixed(2),
    `"${(t.description || '').replace(/"/g, '""')}"`,
  ]);

  const csv = [headers.join(','), ...rows.map((r) => r.join(','))].join('\n');
  res.setHeader('Content-Type', 'text/csv');
  res.setHeader('Content-Disposition', 'attachment; filename="pennywise_transactions.csv"');
  return res.send(csv);
});

// ----------------- SETTINGS ENDPOINTS -----------------
app.get('/api/settings', (_req: Request, res: Response) => {
  return successResponse(res, db.getSettings());
});

app.put('/api/settings', (req: Request, res: Response) => {
  const updated = db.updateSettings(req.body);
  return successResponse(res, updated, 'Settings updated successfully');
});

// ----------------- USER FRONTEND TEMPLATE ROUTES -----------------
app.get('/', (_req: Request, res: Response) => {
  res.setHeader('Content-Type', 'text/html; charset=utf-8');
  res.send(renderPage('dashboard', 'Dashboard'));
});

app.get('/dashboard', (_req: Request, res: Response) => {
  res.setHeader('Content-Type', 'text/html; charset=utf-8');
  res.send(renderPage('dashboard', 'Dashboard'));
});

app.get('/transactions', (_req: Request, res: Response) => {
  res.setHeader('Content-Type', 'text/html; charset=utf-8');
  res.send(renderPage('transactions', 'Transactions'));
});

app.get('/budgets', (_req: Request, res: Response) => {
  res.setHeader('Content-Type', 'text/html; charset=utf-8');
  res.send(renderPage('budgets', 'Budgets'));
});

app.get('/categories', (_req: Request, res: Response) => {
  res.setHeader('Content-Type', 'text/html; charset=utf-8');
  res.send(renderPage('categories', 'Categories'));
});

app.get('/analytics', (_req: Request, res: Response) => {
  res.setHeader('Content-Type', 'text/html; charset=utf-8');
  res.send(renderPage('analytics', 'Analytics'));
});

app.get('/goals', (_req: Request, res: Response) => {
  res.setHeader('Content-Type', 'text/html; charset=utf-8');
  res.send(renderPage('goals', 'Savings Goals'));
});

app.get('/settings', (_req: Request, res: Response) => {
  res.setHeader('Content-Type', 'text/html; charset=utf-8');
  res.send(renderPage('settings', 'Settings'));
});

async function startServer() {
  if (process.env.NODE_ENV !== 'production') {
    try {
      const { createServer: createViteServer } = await import('vite');
      const vite = await createViteServer({
        server: { middlewareMode: true },
        appType: 'custom',
      });
      app.use(vite.middlewares);
    } catch (e) {
      console.warn('Vite dev middleware not mounted:', e);
    }
  }

  // 404 fallback for unmatched page routes
  app.use((req: Request, res: Response) => {
    if (req.path.startsWith('/api')) {
      return errorResponse(res, 'API endpoint not found', 404);
    }
    res.status(404).setHeader('Content-Type', 'text/html; charset=utf-8');
    res.send(renderPage('404', 'Page Not Found'));
  });

  // Start Server
  app.listen(PORT, '0.0.0.0', () => {
    console.log(`🚀 PennyWise Server running on http://0.0.0.0:${PORT}`);
  });
}

startServer();
