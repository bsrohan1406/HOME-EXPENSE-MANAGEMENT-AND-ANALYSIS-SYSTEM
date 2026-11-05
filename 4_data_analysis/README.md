# PennyWise - Data Analysis Package

This package contains the financial analysis, statistics calculation, and budgeting intelligence algorithms.

## Contents
- `data_analysis.py`: Original Python data analysis module for pandas/numpy computation, statistical aggregation, and trend analysis.
- `finance.ts`: Pure TypeScript finance calculation engine:
  - Budget status & overrun calculation
  - Monthly net savings & savings rate formulas
  - Category percentage breakdowns
  - Statistical calculations (Mean, Median, Standard Deviation)
  - Essential vs Discretionary expense ratios
- `finance.test.ts`: Automated unit test suite verifying accuracy across financial algorithms.
- `analysis_adapter.py`: Python adapter connecting database models to the analysis engine.
