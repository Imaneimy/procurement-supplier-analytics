# Text to paste into datascienceportfol.io

## Title
Procurement & Supplier Performance Analytics

## Short description (project card)
Procurement analytics project inspired by my work at Orange Maroc: tested Python + SQL data pipeline, supplier scorecard, budget tracking and a 4-page dashboard design for Power BI.

## About this project
At Orange Maroc I built 15+ procurement dashboards and automated a monthly report from 2 days to 30 minutes. This project rebuilds that workflow from scratch, on synthetic data, so I can show it publicly.

- Designed a realistic synthetic dataset: 45 suppliers, 6,000 purchase orders, 7 department budgets, with real-world defects injected on purpose
- Built 6 data quality checks (duplicates, negative amounts, missing departments, invoice vs PO mismatches) run before every refresh
- Modelled a star schema (2 facts, 4 dimensions + date table) in SQL and exported it for Power BI
- Wrote 25+ DAX measures and parameterised Power Query: YoY, YTD, weighted supplier score /100, Pareto 80/20, conditional formatting, dynamic headline
- Designed a 4-page dashboard (Overview, Suppliers, Budget, Data Quality). The visuals below are the design mockup generated from the data; the Power BI version is in progress
- Key insights: 78% on-time delivery, 11.9 M MAD invoiced above PO amounts, 4 departments over budget, 20 suppliers carrying 80% of spend
- 18 pytest tests, plus 11 test cases to validate every DAX measure against SQL

## Skills / tags
Power BI · DAX · Power Query · Data Modeling · SQL · Python · ETL · Data Quality · KPI Design

## Images
cover: powerbi/maquette/01_overview.png
then: 02_suppliers.png, 03_budget.png, 04_data_quality.png
