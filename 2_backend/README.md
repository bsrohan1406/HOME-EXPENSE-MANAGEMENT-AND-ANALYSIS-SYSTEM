# PennyWise - Backend Package

This package includes both the production Node.js/TypeScript Express server (active runtime) and the Python Flask backend codebase.

## Contents
- `server.ts`: Full-stack Express REST API providing:
  - `/api/categories` (GET, POST, PUT, DELETE)
  - `/api/transactions` (GET, POST, PUT, DELETE, filtering)
  - `/api/budgets` (GET, POST, PUT, DELETE)
  - `/api/goals` (GET, POST, PUT, DELETE, contribute)
  - `/api/analytics/summary`
  - `/api/analytics/monthly`
  - `/api/analytics/categories`
  - `/api/analytics/statistical`
  - `/api/analytics/chart/:chartName` (Dynamic SVG generator)
  - `/api/export/csv`
  - `/api/settings`
- `src/server/db.ts`: Persistent structured database engine with automatic seed data and ACID-like file writes.
- `PennyWise_Backend_Python/`: Original Python/Flask implementation including routes, services, configs, and unit tests.
