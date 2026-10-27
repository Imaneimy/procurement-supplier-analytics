"""
Maquette visuelle des 4 pages du dashboard, à reproduire dans Power BI.
Ce ne sont PAS des captures Power BI : ne pas les publier comme telles.
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import FancyBboxPatch

HERE = Path(__file__).resolve().parent
DATA = HERE.parent / "data"
ORANGE, NAVY, GREEN, GREY, RED, BG = "#FF7900", "#1D3557", "#2A9D8F", "#A8B2C1", "#D62828", "#F3F2F1"

po = pd.read_csv(DATA / "fact_purchase_order.csv", parse_dates=["order_date"])
sup = pd.read_csv(DATA / "dim_supplier.csv")
bud = pd.read_csv(DATA / "fact_budget.csv")
dq = pd.read_csv(DATA / "dq_results.csv")
po["month"] = po["order_date"].dt.strftime("%Y-%m")
po["quarter"] = po["order_date"].dt.to_period("Q").astype(str)
delivered = po[po["is_delivered"]]

# --- same logic as the DAX measures ---
total = po["po_amount_mad"].sum()
on_time = (delivered["on_time"] == True).mean()
overbilled = po.loc[~po["invoice_match"] & (po["invoice_gap_mad"] > 0), "invoice_gap_mad"].sum()
off_contract = po.merge(sup, on="supplier_id").query("~has_framework_contract")["po_amount_mad"].sum() / total

g = po.groupby("supplier_id")
score = pd.DataFrame({
    "orders": g.size(),
    "spend": g["po_amount_mad"].sum(),
    "on_time": delivered.groupby("supplier_id")["on_time"].apply(lambda s: (s == True).mean()),
    "quality": 1 - g["quality_issue"].mean(),
    "invoice": g["invoice_match"].mean(),
}).join(sup.set_index("supplier_id")[["category"]])
score["score"] = 100 * (0.4 * score["on_time"] + 0.3 * score["quality"] + 0.3 * score["invoice"])
score = score[score["orders"] >= 20]

budget = (bud.groupby("department")["budget_mad"].sum().to_frame()
          .join(po.groupby("department")["po_amount_mad"].sum().rename("spend")))
budget["pct"] = budget["spend"] / budget["budget_mad"]
over = int((budget["pct"] > 1).sum())

pareto = g["po_amount_mad"].sum().rename("spend").sort_values(ascending=False).to_frame()
pareto["cum"] = pareto["spend"].cumsum() / pareto["spend"].sum()
n80 = int((pareto["cum"] < 0.8).sum()) + 1


def page(title, active):
    fig = plt.figure(figsize=(16, 9), facecolor=BG)
    fig.text(0.02, 0.955, "Procurement & Supplier Performance", fontsize=20, color=NAVY, weight="bold")
    fig.text(0.02, 0.925, f"{title}  ·  Jan 2024 – Jun 2025  ·  synthetic data", fontsize=11, color="#6c757d")
    for i, name in enumerate(["Overview", "Suppliers", "Budget", "Data Quality"]):
        x = 0.60 + i * 0.095
        fig.patches.append(FancyBboxPatch((x, 0.935), 0.085, 0.035, boxstyle="round,pad=0.003",
                                          transform=fig.transFigure,
                                          fc=ORANGE if name == active else "white", ec=GREY, lw=0.6))
        fig.text(x + 0.0425, 0.952, name, ha="center", va="center", fontsize=10,
                 color="white" if name == active else NAVY)
    fig.text(0.99, 0.01, "Dashboard design mockup · generated from the project data · Power BI version in progress",
             ha="right", fontsize=8, color="#9aa0a6", style="italic")
    return fig


def panel(fig, rect, title=None):
    ax = fig.add_axes(rect)
    ax.set_facecolor("white")
    for s in ax.spines.values():
        s.set_visible(False)
    ax.tick_params(colors=NAVY, labelsize=9)
    if title:
        ax.set_title(title, loc="left", fontsize=11, color=NAVY, weight="bold", pad=10)
    fig.patches.append(FancyBboxPatch((rect[0] - 0.012, rect[1] - 0.05), rect[2] + 0.024, rect[3] + 0.09,
                                      boxstyle="round,pad=0.002", transform=fig.transFigure,
                                      fc="white", ec="#e1dfdd", lw=0.8, zorder=-1))
    return ax


def card(fig, x, y, w, value, label, color=ORANGE):
    fig.patches.append(FancyBboxPatch((x, y), w, 0.11, boxstyle="round,pad=0.003",
                                      transform=fig.transFigure, fc="white", ec="#e1dfdd", lw=0.8))
    fig.text(x + 0.012, y + 0.05, value, fontsize=22, color=color, weight="bold")
    fig.text(x + 0.012, y + 0.018, label, fontsize=9.5, color="#6c757d")


def save(fig, name):
    fig.savefig(HERE / name, dpi=110, facecolor=BG)
    plt.close(fig)


# ---------------- Page 1: Overview ----------------
fig = page("Overview", "Overview")
kpis = [
    (f"{total / 1e6:,.0f} M", "Total spend (MAD)"),
    (f"{len(po):,}", "Purchase orders"),
    (f"{on_time:.1%}", "On-time delivery"),
    (f"{delivered['lead_time_days'].mean():.1f} d", "Avg lead time"),
    (f"{po['invoice_match'].mean():.1%}", "Invoices matching PO"),
    (f"{off_contract:.1%}", "Off-contract spend"),
]
for i, (v, l) in enumerate(kpis):
    card(fig, 0.02 + i * 0.163, 0.76, 0.152, v, l)
fig.patches.append(FancyBboxPatch((0.02, 0.675), 0.96, 0.055, boxstyle="round,pad=0.003",
                                  transform=fig.transFigure, fc="#FFF4EB", ec=ORANGE, lw=1))
fig.text(0.035, 0.695, f"⚠  {overbilled / 1e6:.1f} M MAD invoiced above PO  ·  {over} departments over budget  ·  "
         f"{n80} suppliers carry 80% of spend", fontsize=12, color=NAVY, weight="bold")

m = po.groupby("month").agg(spend=("po_amount_mad", "sum"))
m["on_time"] = delivered.groupby("month")["on_time"].apply(lambda s: (s == True).mean())
ax = panel(fig, [0.05, 0.1, 0.52, 0.48], "Monthly spend (M MAD) and on-time delivery %")
ax.bar(m.index, m["spend"] / 1e6, color=GREY)
ax.tick_params(axis="x", rotation=60, labelsize=8)
ax2 = ax.twinx()
ax2.plot(m.index, m["on_time"] * 100, color=ORANGE, marker="o", lw=2)
ax2.set_ylim(0, 100)
for s in ax2.spines.values():
    s.set_visible(False)
ax2.tick_params(colors=ORANGE, labelsize=9)

c = po.groupby("category")["po_amount_mad"].sum().sort_values() / 1e6
ax = panel(fig, [0.71, 0.1, 0.26, 0.48], "Spend by category (M MAD)")
bars = ax.barh(c.index, c.values, color=NAVY)
ax.bar_label(bars, fmt="%.0f", fontsize=9, color=NAVY, padding=3)
ax.set_xticks([])
save(fig, "01_overview.png")

# ---------------- Page 2: Suppliers ----------------
fig = page("Suppliers", "Suppliers")
ax = panel(fig, [0.05, 0.52, 0.45, 0.32], f"Pareto: {n80} of {len(pareto)} suppliers carry 80% of spend")
ax.bar(range(len(pareto)), pareto["spend"] / 1e6,
       color=[ORANGE if i < n80 else GREY for i in range(len(pareto))])
ax.set_xticks([])
ax2 = ax.twinx()
ax2.plot(range(len(pareto)), pareto["cum"] * 100, color=NAVY, lw=1.8)
ax2.axhline(80, color=NAVY, ls=":", lw=1)
ax2.set_ylim(0, 105)
for s in ax2.spines.values():
    s.set_visible(False)

ax = panel(fig, [0.05, 0.08, 0.45, 0.33], "On-time vs invoice accuracy (bubble = spend)")
ax.scatter(score["on_time"] * 100, score["invoice"] * 100, s=score["spend"] / score["spend"].max() * 900,
           c=[RED if s < 70 else ORANGE if s < 85 else GREEN for s in score["score"]], alpha=0.7, ec="white")
ax.set_xlabel("On-time %", color=NAVY, fontsize=9)
ax.set_ylabel("Invoice match %", color=NAVY, fontsize=9)
ax.grid(alpha=0.2)

ax = panel(fig, [0.55, 0.08, 0.42, 0.76], "Supplier scorecard /100 (lowest first)")
ax.axis("off")
t = score.nsmallest(16, "score")
rows = [[i, r.category, f"{r.spend / 1e6:.1f}", f"{r.on_time:.0%}", f"{r.quality:.0%}", f"{r.invoice:.0%}",
         f"{r.score:.0f}"] for i, r in t.iterrows()]
tbl = ax.table(cellText=rows, colLabels=["Supplier", "Category", "Spend M", "On-time", "Quality", "Invoice", "Score"],
               loc="upper center", cellLoc="left", colWidths=[.12, .3, .11, .11, .11, .11, .1])
tbl.auto_set_font_size(False)
tbl.set_fontsize(9)
tbl.scale(1, 1.55)
for (r, col), cell in tbl.get_celld().items():
    cell.set_edgecolor("#eeeeee")
    if r == 0:
        cell.set_facecolor(NAVY)
        cell.get_text().set_color("white")
    elif col == 6:
        s = float(cell.get_text().get_text())
        cell.set_facecolor(RED if s < 70 else ORANGE if s < 85 else GREEN)
        cell.get_text().set_color("white")
save(fig, "02_suppliers.png")

# ---------------- Page 3: Budget ----------------
fig = page("Budget", "Budget")
h1 = lambda y: po[(po["order_date"].dt.year == y) & (po["order_date"].dt.month <= 6)]["po_amount_mad"].sum()
card(fig, 0.02, 0.76, 0.2, f"{over}", "Departments over budget", RED)
card(fig, 0.24, 0.76, 0.2, f"{(budget['spend'].sum() - budget['budget_mad'].sum()) / 1e6:+,.0f} M",
     "Budget variance (MAD)", RED)
card(fig, 0.46, 0.76, 0.2, f"{h1(2025) / h1(2024) - 1:+.1%}", "Spend YoY (Jan–Jun 2025)", NAVY)

b = budget.sort_values("pct")
ax = panel(fig, [0.13, 0.1, 0.33, 0.52], "Budget consumed per department")
bars = ax.barh(b.index, b["pct"] * 100,
               color=[RED if p > 1 else ORANGE if p > 0.9 else GREY for p in b["pct"]])
ax.bar_label(bars, fmt="%.0f%%", fontsize=9, color=NAVY, padding=3)
ax.axvline(100, color=NAVY, ls="--", lw=1)
ax.set_xlim(0, 135)
ax.set_xticks([])

q = bud.groupby("quarter")["budget_mad"].sum().to_frame().join(po.groupby("quarter")["po_amount_mad"].sum())
ax = panel(fig, [0.55, 0.1, 0.42, 0.52], "Budget vs spend per quarter (M MAD)")
x = range(len(q))
ax.bar([i - 0.2 for i in x], q["budget_mad"] / 1e6, width=0.4, color=GREY, label="Budget")
ax.bar([i + 0.2 for i in x], q["po_amount_mad"] / 1e6, width=0.4, color=ORANGE, label="Spend")
ax.set_xticks(list(x), q.index)
ax.legend(frameon=False, fontsize=9)
save(fig, "03_budget.png")

# ---------------- Page 4: Data Quality ----------------
fig = page("Data Quality", "Data Quality")
card(fig, 0.02, 0.76, 0.2, f"{(dq['status'] == 'PASS').sum()} / {len(dq)}", "Checks passed", GREEN)
card(fig, 0.24, 0.76, 0.2, f"{dq.loc[dq['status'] == 'FAIL', 'rows_failed'].sum()}", "Rows fixed before load", ORANGE)
card(fig, 0.46, 0.76, 0.2, f"{dq.loc[dq['status'] == 'WARN', 'rows_failed'].sum()}", "Invoices flagged to business", RED)
ax = panel(fig, [0.05, 0.25, 0.9, 0.4], "Checks run before every refresh")
ax.axis("off")
rows = dq[["check_id", "rule", "rows_failed", "pct_failed", "status"]].values.tolist()
tbl = ax.table(cellText=rows, colLabels=["Check", "Rule", "Rows failed", "% failed", "Status"],
               loc="upper center", cellLoc="left", colWidths=[.1, .5, .13, .13, .14])
tbl.auto_set_font_size(False)
tbl.set_fontsize(11)
tbl.scale(1, 2.2)
colors = {"PASS": GREEN, "WARN": ORANGE, "FAIL": RED}
for (r, col), cell in tbl.get_celld().items():
    cell.set_edgecolor("#eeeeee")
    if r == 0:
        cell.set_facecolor(NAVY)
        cell.get_text().set_color("white")
    elif col == 4:
        cell.set_facecolor(colors[cell.get_text().get_text()])
        cell.get_text().set_color("white")
fig.text(0.05, 0.1, "Duplicates removed, sign errors corrected, missing departments set to 'Unassigned', "
         "invoice gaps reported to the business.", fontsize=11, color=NAVY, style="italic")
save(fig, "04_data_quality.png")
print("Maquettes écrites dans", HERE)
