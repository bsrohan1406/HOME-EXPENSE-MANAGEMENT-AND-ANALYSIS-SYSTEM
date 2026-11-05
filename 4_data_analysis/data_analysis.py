import os

def create_analysis_module():
    # Create analysis directory
    os.makedirs("analysis", exist_ok=True)
    
    files = {
        "analysis/__init__.py": '''from flask import Blueprint

analytics_bp = Blueprint('analytics', __name__, url_prefix='/api/analytics')

from analysis import routes
''',
        
        "analysis/data_loader.py": '''import pandas as pd
import numpy as np
from app import db
from sqlalchemy import text

def load_transactions_df():
    query = text("""
        SELECT t.id, t.kind, t.amount, t.transaction_date, t.category_id, t.description, c.name as category_name
        FROM transactions t
        LEFT JOIN categories c ON t.category_id = c.id
    """)
    df = pd.read_sql(query, db.engine)
    if df.empty:
        return pd.DataFrame(columns=['id', 'kind', 'amount', 'transaction_date', 'category_id', 'description', 'category_name'])
    df['amount'] = pd.to_numeric(df['amount'], errors='coerce').fillna(0.0)
    df['transaction_date'] = pd.to_datetime(df['transaction_date'], errors='coerce')
    df['kind'] = df['kind'].str.lower().str.strip()
    df = df[df['kind'].isin(['income', 'expense'])]
    df = df[df['amount'] > 0]
    return df

def load_budgets_df():
    query = text("SELECT id, month, category_id, amount FROM budgets")
    df = pd.read_sql(query, db.engine)
    if df.empty:
        return pd.DataFrame(columns=['id', 'month', 'category_id', 'amount'])
    df['amount'] = pd.to_numeric(df['amount'], errors='coerce').fillna(0.0)
    return df

def load_savings_goals_df():
    query = text("SELECT id, name, target_amount, current_amount FROM savings_goals")
    df = pd.read_sql(query, db.engine)
    if df.empty:
        return pd.DataFrame(columns=['id', 'name', 'target_amount', 'current_amount'])
    df['target_amount'] = pd.to_numeric(df['target_amount'], errors='coerce').fillna(0.0)
    df['current_amount'] = pd.to_numeric(df['current_amount'], errors='coerce').fillna(0.0)
    return df

def load_categories_df():
    query = text("SELECT id, name, kind, color FROM categories")
    df = pd.read_sql(query, db.engine)
    return df
''',

        "analysis/financial_summary.py": '''import numpy as np
from analysis.data_loader import load_transactions_df

def calculate_financial_summary():
    df = load_transactions_df()
    if df.empty:
        return {
            "total_income": 0.0, "total_expenses": 0.0,
            "net_savings": 0.0, "savings_rate": 0.0,
            "average_monthly_expenses": 0.0
        }
    total_income = float(df[df['kind'] == 'income']['amount'].sum())
    total_expenses = float(df[df['kind'] == 'expense']['amount'].sum())
    net_savings = total_income - total_expenses
    savings_rate = (net_savings / total_income * 100) if total_income > 0 else 0.0
    
    df['month'] = df['transaction_date'].dt.to_period('M')
    monthly_expenses = df[df['kind'] == 'expense'].groupby('month')['amount'].sum()
    avg_monthly_expenses = float(monthly_expenses.mean()) if not monthly_expenses.empty else 0.0
    
    return {
        "total_income": round(total_income, 2),
        "total_expenses": round(total_expenses, 2),
        "net_savings": round(net_savings, 2),
        "savings_rate": round(savings_rate, 2),
        "average_monthly_expenses": round(avg_monthly_expenses, 2)
    }
''',

        "analysis/monthly_analysis.py": '''import pandas as pd
import numpy as np
from analysis.data_loader import load_transactions_df

def calculate_monthly_analysis():
    df = load_transactions_df()
    if df.empty:
        return []
    df['month_str'] = df['transaction_date'].dt.strftime('%Y-%m')
    monthly = df.groupby(['month_str', 'kind'])['amount'].sum().unstack(fill_value=0.0)
    if 'income' not in monthly.columns: monthly['income'] = 0.0
    if 'expense' not in monthly.columns: monthly['expense'] = 0.0
    monthly = monthly.reset_index()
    monthly['savings'] = monthly['income'] - monthly['expense']
    monthly = monthly.sort_values('month_str')
    monthly['spending_increase'] = monthly['expense'].diff() > 0
    monthly['spending_diff'] = monthly['expense'].diff().fillna(0.0)
    
    result = []
    for _, row in monthly.iterrows():
        result.append({
            "month": row['month_str'],
            "income": round(float(row['income']), 2),
            "expense": round(float(row['expense']), 2),
            "savings": round(float(row['savings']), 2),
            "spending_increased": bool(row['spending_increase']),
            "spending_diff": round(float(row['spending_diff']), 2)
        })
    return result
''',

        "analysis/category_analysis.py": '''import pandas as pd
import numpy as np
from analysis.data_loader import load_transactions_df

def calculate_category_analysis():
    df = load_transactions_df()
    if df.empty:
        return {"highest_spending_category": None, "categories": []}
    expense_df = df[df['kind'] == 'expense']
    if expense_df.empty:
        return {"highest_spending_category": None, "categories": []}
    total_expenses = expense_df['amount'].sum()
    cat_group = expense_df.groupby(['category_id', 'category_name'])['amount'].sum().reset_index()
    cat_group = cat_group.sort_values(by='amount', ascending=False)
    cat_group['rank'] = cat_group['amount'].rank(ascending=False, method='min').astype(int)
    cat_group['percentage'] = (cat_group['amount'] / total_expenses * 100) if total_expenses > 0 else 0.0
    highest_category = cat_group.iloc[0]['category_name'] if not cat_group.empty else None
    
    categories_list = []
    for _, row in cat_group.iterrows():
        categories_list.append({
            "category_id": int(row['category_id']) if pd.notna(row['category_id']) else None,
            "category_name": row['category_name'] or "Uncategorized",
            "total_expense": round(float(row['amount']), 2),
            "percentage_contribution": round(float(row['percentage']), 2),
            "rank": int(row['rank'])
        })
    return {"highest_spending_category": highest_category, "categories": categories_list}
''',

        "analysis/budget_analysis.py": '''import pandas as pd
import numpy as np
from analysis.data_loader import load_budgets_df, load_transactions_df, load_categories_df

def calculate_budget_analysis():
    budgets_df = load_budgets_df()
    transactions_df = load_transactions_df()
    categories_df = load_categories_df()
    if budgets_df.empty:
        return []
    expense_df = transactions_df[transactions_df['kind'] == 'expense'].copy()
    if not expense_df.empty:
        expense_df['month'] = expense_df['transaction_date'].dt.strftime('%Y-%m')
        actuals = expense_df.groupby(['month', 'category_id'])['amount'].sum().reset_index()
        actuals.rename(columns={'amount': 'actual_spent'}, inplace=True)
    else:
        actuals = pd.DataFrame(columns=['month', 'category_id', 'actual_spent'])
        
    merged = pd.merge(budgets_df, actuals, on=['month', 'category_id'], how='left')
    merged['actual_spent'] = merged['actual_spent'].fillna(0.0)
    merged = pd.merge(merged, categories_df, left_on='category_id', right_on='id', how='left')
    
    results = []
    for _, row in merged.iterrows():
        budget_amt = float(row['amount'])
        spent_amt = float(row['actual_spent'])
        remaining = budget_amt - spent_amt
        utilization = (spent_amt / budget_amt * 100) if budget_amt > 0 else (100.0 if spent_amt > 0 else 0.0)
        overspending = max(0.0, spent_amt - budget_amt)
        
        if spent_amt > budget_amt:
            status = "Over Budget"
        elif utilization >= 80.0:
            status = "Almost at Limit"
        else:
            status = "On Track"
            
        results.append({
            "budget_id": int(row['id']),
            "month": row['month'],
            "category_name": row.get('name', 'Unknown'),
            "budget_amount": round(budget_amt, 2),
            "actual_spending": round(spent_amt, 2),
            "remaining_budget": round(remaining, 2),
            "budget_utilization_percentage": round(utilization, 2),
            "overspending_amount": round(overspending, 2),
            "status": status
        })
    return results
''',

        "analysis/savings_analysis.py": '''import pandas as pd
import numpy as np
from analysis.data_loader import load_savings_goals_df

def calculate_savings_analysis():
    df = load_savings_goals_df()
    if df.empty:
        return {"total_savings": 0.0, "goals": []}
    total_savings = float(df['current_amount'].sum())
    goals = []
    for _, row in df.iterrows():
        target = float(row['target_amount'])
        current = float(row['current_amount'])
        remaining = max(0.0, target - current)
        completion = (current / target * 100) if target > 0 else (100.0 if current > 0 else 0.0)
        goals.append({
            "goal_id": int(row['id']),
            "name": row['name'],
            "target_amount": round(target, 2),
            "current_amount": round(current, 2),
            "remaining_amount": round(remaining, 2),
            "goal_completion_percentage": round(completion, 2)
        })
    return {"total_savings": round(total_savings, 2), "goals": goals}
''',

        "analysis/charts.py": '''import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
from analysis.category_analysis import calculate_category_analysis
from analysis.monthly_analysis import calculate_monthly_analysis
from analysis.budget_analysis import calculate_budget_analysis

def generate_pie_chart_categories():
    cat_data = calculate_category_analysis()
    categories = cat_data.get("categories", [])
    fig, ax = plt.subplots(figsize=(6, 6))
    if not categories:
        ax.text(0.5, 0.5, "No Expense Data Available", ha='center', va='center')
    else:
        labels = [c['category_name'] for c in categories]
        sizes = [c['total_expense'] for c in categories]
        wedges, texts, autotexts = ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140, wedgeprops=dict(width=0.4, edgecolor='w'))
        plt.setp(autotexts, size=9, weight="bold")
        ax.set_title("Expense Distribution by Category", fontsize=12, fontweight='bold', pad=15)
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=100)
    buf.seek(0)
    plt.close(fig)
    return buf

def generate_monthly_income_expense_bar():
    monthly_data = calculate_monthly_analysis()
    fig, ax = plt.subplots(figsize=(8, 5))
    if not monthly_data:
        ax.text(0.5, 0.5, "No Monthly Data Available", ha='center', va='center')
    else:
        months = [m['month'] for m in monthly_data]
        incomes = [m['income'] for m in monthly_data]
        expenses = [m['expense'] for m in monthly_data]
        x = range(len(months))
        width = 0.35
        ax.bar([i - width/2 for i in x], incomes, width, label='Income', color='#2ecc71')
        ax.bar([i + width/2 for i in x], expenses, width, label='Expenses', color='#e74c3c')
        ax.set_xlabel('Month', fontweight='bold')
        ax.set_ylabel('Amount ($)', fontweight='bold')
        ax.set_title('Monthly Income vs Expenses', fontsize=12, fontweight='bold', pad=15)
        ax.set_xticks(x)
        ax.set_xticklabels(months, rotation=45)
        ax.legend()
        ax.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=100)
    buf.seek(0)
    plt.close(fig)
    return buf

def generate_monthly_savings_line():
    monthly_data = calculate_monthly_analysis()
    fig, ax = plt.subplots(figsize=(8, 4.5))
    if not monthly_data:
        ax.text(0.5, 0.5, "No Savings Data Available", ha='center', va='center')
    else:
        months = [m['month'] for m in monthly_data]
        savings = [m['savings'] for m in monthly_data]
        ax.plot(months, savings, marker='o', color='#3498db', linewidth=2.5, markersize=6)
        ax.axhline(0, color='grey', linestyle='--', linewidth=1)
        ax.set_xlabel('Month', fontweight='bold')
        ax.set_ylabel('Net Savings ($)', fontweight='bold')
        ax.set_title('Monthly Savings Trend', fontsize=12, fontweight='bold', pad=15)
        plt.xticks(rotation=45)
        ax.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=100)
    buf.seek(0)
    plt.close(fig)
    return buf

def generate_budget_vs_actual_bar():
    budget_data = calculate_budget_analysis()
    fig, ax = plt.subplots(figsize=(8, 5))
    if not budget_data:
        ax.text(0.5, 0.5, "No Budget Data Available", ha='center', va='center')
    else:
        labels = [f"{b['category_name']} ({b['month']})" for b in budget_data]
        budgets = [b['budget_amount'] for b in budget_data]
        actuals = [b['actual_spending'] for b in budget_data]
        x = range(len(labels))
        width = 0.35
        ax.bar([i - width/2 for i in x], budgets, width, label='Budget', color='#9b59b6')
        ax.bar([i + width/2 for i in x], actuals, width, label='Actual Spending', color='#e67e22')
        ax.set_xlabel('Category & Month', fontweight='bold')
        ax.set_ylabel('Amount ($)', fontweight='bold')
        ax.set_title('Budget vs Actual Spending', fontsize=12, fontweight='bold', pad=15)
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=45, ha='right')
        ax.legend()
        ax.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=100)
    buf.seek(0)
    plt.close(fig)
    return buf

def generate_budget_utilization_bar():
    budget_data = calculate_budget_analysis()
    fig, ax = plt.subplots(figsize=(8, 5))
    if not budget_data:
        ax.text(0.5, 0.5, "No Budget Utilization Data", ha='center', va='center')
    else:
        labels = [f"{b['category_name']} ({b['month']})" for b in budget_data]
        utilizations = [b['budget_utilization_percentage'] for b in budget_data]
        colors = ['#e74c3c' if u > 100 else ('#f1c40f' if u >= 80 else '#2ecc71') for u in utilizations]
        ax.barh(labels, utilizations, color=colors)
        ax.axvline(100, color='red', linestyle='--', label='100% Limit')
        ax.set_xlabel('Utilization Percentage (%)', fontweight='bold')
        ax.set_ylabel('Category & Month', fontweight='bold')
        ax.set_title('Budget Utilization by Category', fontsize=12, fontweight='bold', pad=15)
        ax.legend()
        ax.grid(axis='x', linestyle='--', alpha=0.7)
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=100)
    buf.seek(0)
    plt.close(fig)
    return buf
''',

        "analysis/routes.py": '''from flask import jsonify, send_file
from analysis import analytics_bp
from analysis.financial_summary import calculate_financial_summary
from analysis.monthly_analysis import calculate_monthly_analysis
from analysis.category_analysis import calculate_category_analysis
from analysis.budget_analysis import calculate_budget_analysis
from analysis.savings_analysis import calculate_savings_analysis
from analysis.charts import (
    generate_pie_chart_categories,
    generate_monthly_income_expense_bar,
    generate_monthly_savings_line,
    generate_budget_vs_actual_bar,
    generate_budget_utilization_bar
)

@analytics_bp.route('/summary', methods=['GET'])
def api_financial_summary():
    try:
        return jsonify({"status": "success", "data": calculate_financial_summary()}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@analytics_bp.route('/monthly', methods=['GET'])
def api_monthly_analysis():
    try:
        return jsonify({"status": "success", "data": calculate_monthly_analysis()}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@analytics_bp.route('/categories', methods=['GET'])
def api_category_analysis():
    try:
        return jsonify({"status": "success", "data": calculate_category_analysis()}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@analytics_bp.route('/budget-status', methods=['GET'])
def api_budget_status():
    try:
        return jsonify({"status": "success", "data": calculate_budget_analysis()}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@analytics_bp.route('/savings', methods=['GET'])
def api_savings_analysis():
    try:
        return jsonify({"status": "success", "data": calculate_savings_analysis()}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@analytics_bp.route('/chart/categories', methods=['GET'])
def api_chart_categories():
    return send_file(generate_pie_chart_categories(), mimetype='image/png')

@analytics_bp.route('/chart/monthly-income-expense', methods=['GET'])
def api_chart_monthly_income_expense():
    return send_file(generate_monthly_income_expense_bar(), mimetype='image/png')

@analytics_bp.route('/chart/monthly-savings', methods=['GET'])
def api_chart_monthly_savings():
    return send_file(generate_monthly_savings_line(), mimetype='image/png')

@analytics_bp.route('/chart/budget-vs-actual', methods=['GET'])
def api_chart_budget_vs_actual():
    return send_file(generate_budget_vs_actual_bar(), mimetype='image/png')

@analytics_bp.route('/chart/budget-utilization', methods=['GET'])
def api_chart_budget_utilization():
    return send_file(generate_budget_utilization_bar(), mimetype='image/png')
'''
    }
    
    for filepath, content in files.items():
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content.strip())
        print(f"✅ Created file: {filepath}")
        
    print("\n🎉 All analysis module files have been successfully generated inside the 'analysis/' folder!")

if __name__ == "__main__":
    create_analysis_module()