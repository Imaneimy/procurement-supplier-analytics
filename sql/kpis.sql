-- name: overview
SELECT
    COUNT(*)                                                         AS purchase_orders,
    ROUND(SUM(po_amount_mad) / 1e6, 1)                               AS total_spend_m_mad,
    ROUND(100.0 * AVG(CASE WHEN is_delivered THEN on_time END), 1)   AS on_time_rate_pct,
    ROUND(AVG(CASE WHEN is_delivered THEN lead_time_days END), 1)    AS avg_lead_time_days,
    ROUND(100.0 * AVG(invoice_match), 1)                             AS invoice_match_pct,
    ROUND(SUM(CASE WHEN NOT invoice_match THEN invoice_gap_mad END) / 1e6, 2) AS overbilled_m_mad
FROM fact_purchase_order;

-- name: supplier_scorecard
-- Score /100: on-time 40%, quality 30%, invoice accuracy 30%
SELECT
    s.supplier_id,
    s.category,
    s.city,
    COUNT(*)                                                           AS orders,
    ROUND(SUM(p.po_amount_mad) / 1e6, 2)                               AS spend_m_mad,
    ROUND(100.0 * AVG(CASE WHEN p.is_delivered THEN p.on_time END), 1) AS on_time_pct,
    ROUND(100.0 * (1 - AVG(p.quality_issue)), 1)                       AS quality_pct,
    ROUND(100.0 * AVG(p.invoice_match), 1)                             AS invoice_ok_pct,
    ROUND(0.4 * 100.0 * AVG(CASE WHEN p.is_delivered THEN p.on_time END)
        + 0.3 * 100.0 * (1 - AVG(p.quality_issue))
        + 0.3 * 100.0 * AVG(p.invoice_match), 1)                        AS score
FROM fact_purchase_order p
JOIN dim_supplier s USING (supplier_id)
GROUP BY s.supplier_id
HAVING COUNT(*) >= 20
ORDER BY score DESC;

-- name: spend_by_category
SELECT category,
       ROUND(SUM(po_amount_mad) / 1e6, 1) AS spend_m_mad,
       ROUND(100.0 * AVG(CASE WHEN is_delivered THEN on_time END), 1) AS on_time_pct
FROM fact_purchase_order
GROUP BY category
ORDER BY spend_m_mad DESC;

-- name: monthly_trend
SELECT month,
       ROUND(SUM(po_amount_mad) / 1e6, 1) AS spend_m_mad,
       ROUND(100.0 * AVG(CASE WHEN is_delivered THEN on_time END), 1) AS on_time_pct
FROM fact_purchase_order
GROUP BY month
ORDER BY month;

-- name: budget_consumption
SELECT b.department,
       ROUND(SUM(b.budget_mad) / 1e6, 1)                     AS budget_m_mad,
       ROUND(COALESCE(SUM(p.spend), 0) / 1e6, 1)             AS spend_m_mad,
       ROUND(100.0 * COALESCE(SUM(p.spend), 0) / SUM(b.budget_mad), 1) AS consumed_pct
FROM fact_budget b
LEFT JOIN (SELECT department, quarter, SUM(po_amount_mad) AS spend
           FROM fact_purchase_order GROUP BY department, quarter) p
       ON p.department = b.department AND p.quarter = b.quarter
GROUP BY b.department
ORDER BY consumed_pct DESC;

-- name: off_contract_spend
SELECT ROUND(100.0 * SUM(CASE WHEN NOT s.has_framework_contract THEN p.po_amount_mad END)
             / SUM(p.po_amount_mad), 1) AS off_contract_pct
FROM fact_purchase_order p
JOIN dim_supplier s USING (supplier_id);
