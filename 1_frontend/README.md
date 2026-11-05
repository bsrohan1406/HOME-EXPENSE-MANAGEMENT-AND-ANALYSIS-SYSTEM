# PennyWise - Frontend Package

This package contains the complete user interface for the PennyWise Personal Finance & Analytics application.

## Contents
- `static/css/styles.css`: Complete Dark Modern UI stylesheet with responsive typography, dashboard layout, modals, and toasts.
- `static/js/app.js`: Complete client-side application logic (fixed with null-safe element checks across all viewports).
- `templates/`: Complete Jinja2 / HTML templates:
  - `base.html`: Core layout with sidebar navigation, search bar, topbar, and modal backdrops.
  - `dashboard.html`: Financial overview, stat cards, income vs expenses chart, expense breakdown, and budget previews.
  - `transactions.html`: Transaction ledger, search, filters, and add/edit transaction modals.
  - `budgets.html`: Monthly budget tracker with progress bars and variance status.
  - `categories.html`: Expense and income category management with color badges.
  - `analytics.html`: Comprehensive financial metrics, category breakdowns, and trend charts.
  - `goals.html`: Savings goals tracker with milestone progress and contribution modals.
  - `settings.html`: Currency configuration, monthly budget target, and data export.
  - `404.html`: Not found error page.
- `index.html`: Standalone single-page build of the dashboard.
