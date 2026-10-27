// ============================================================
// Power Query (M) — one query per table.
// 1. Home > Manage Parameters > New: name = DataFolder, type = Text,
//    value = full path to powerbi/data/ WITH the trailing slash
//    e.g. C:\Users\imane\procurement-supplier-analytics\powerbi\data\
// 2. Home > New Source > Blank Query > Advanced Editor, paste one block,
//    and rename the query with the name in the comment above it.
// ============================================================

// ---------- fact_purchase_order ----------
let
    Source   = Csv.Document(File.Contents(DataFolder & "fact_purchase_order.csv"), [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Headers  = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    Typed    = Table.TransformColumnTypes(Headers, {
        {"po_id", type text}, {"supplier_id", type text}, {"department", type text}, {"category", type text},
        {"order_date", type date}, {"promised_date", type date}, {"delivered_date", type date},
        {"po_amount_mad", Currency.Type}, {"invoice_amount_mad", Currency.Type}, {"invoice_gap_mad", Currency.Type},
        {"is_delivered", type logical}, {"on_time", type logical}, {"delay_days", Int64.Type},
        {"lead_time_days", Int64.Type}, {"invoice_match", type logical}, {"quality_issue", type logical}
    }, "en-US")
in
    Typed

// ---------- fact_budget ----------
let
    Source  = Csv.Document(File.Contents(DataFolder & "fact_budget.csv"), [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    Typed   = Table.TransformColumnTypes(Headers, {
        {"department", type text}, {"quarter", type text}, {"budget_mad", Currency.Type}, {"quarter_start", type date}
    }, "en-US")
in
    Typed

// ---------- dim_supplier ----------
let
    Source  = Csv.Document(File.Contents(DataFolder & "dim_supplier.csv"), [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    Typed   = Table.TransformColumnTypes(Headers, {
        {"supplier_id", type text}, {"supplier_name", type text}, {"category", type text},
        {"city", type text}, {"has_framework_contract", type logical}
    }, "en-US")
in
    Typed

// ---------- dim_department ----------
let
    Source  = Csv.Document(File.Contents(DataFolder & "dim_department.csv"), [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    Typed   = Table.TransformColumnTypes(Headers, {{"department", type text}})
in
    Typed

// ---------- dim_date ----------
let
    Source  = Csv.Document(File.Contents(DataFolder & "dim_date.csv"), [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    Typed   = Table.TransformColumnTypes(Headers, {
        {"Date", type date}, {"Year", Int64.Type}, {"Quarter", type text}, {"YearQuarter", type text},
        {"MonthNumber", Int64.Type}, {"Month", type text}, {"YearMonth", type text}
    }, "en-US")
in
    Typed

// ---------- dq_results ----------
let
    Source  = Csv.Document(File.Contents(DataFolder & "dq_results.csv"), [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    Typed   = Table.TransformColumnTypes(Headers, {
        {"check_id", type text}, {"rule", type text}, {"rows_failed", Int64.Type},
        {"pct_failed", type number}, {"status", type text}
    }, "en-US")
in
    Typed
