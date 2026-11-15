"""
Python vasitəsilə PostgreSQL bazasına qoşulma, analitik sorğuların icrası,
qrafiklərin qurulması və satış hesabatının hazırlanması.

Çıxış:
    reports/query_results/*.csv     — hər sorğunun nəticəsi
    reports/sales_report.xlsx       — bütün nəticələr bir Excel faylında
    reports/figures/*.png           — qrafiklər
    reports/sales_report.md         — qısa mətn hesabatı (əsas göstəricilər)
"""
import re
import time

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
from sqlalchemy import create_engine, text

from config import DATABASE_URL, FIGURES_DIR, REPORTS_DIR, SQL_DIR

QUERY_DIR = REPORTS_DIR / "query_results"
QUERY_DIR.mkdir(exist_ok=True)

plt.rcParams.update({
    "figure.dpi": 120, "savefig.dpi": 150, "savefig.bbox": "tight",
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.alpha": 0.3, "font.size": 10,
})
PRIMARY = "#2563eb"
PALETTE = ["#2563eb", "#16a34a", "#f59e0b", "#dc2626", "#7c3aed",
           "#0891b2", "#db2777", "#65a30d", "#ea580c", "#475569"]
azn = mticker.FuncFormatter(lambda x, _: f"{x / 1000:,.0f}k" if abs(x) >= 1000 else f"{x:,.0f}")


def parse_queries(path):
    """'-- name: xxx' markerləri ilə SQL faylını ayrı sorğulara bölür."""
    content = path.read_text(encoding="utf-8")
    parts = re.split(r"^--\s*name:\s*(\w+)\s*$", content, flags=re.M)
    queries = {}
    for name, body in zip(parts[1::2], parts[2::2]):
        lines = body.strip().splitlines()
        desc = lines[0].lstrip("- ").strip() if lines and lines[0].startswith("--") else ""
        sql = "\n".join(l for l in lines if not l.strip().startswith("--")).strip().rstrip(";")
        queries[name] = {"description": desc, "sql": sql}
    return queries


def run_queries(engine, queries):
    results, timings = {}, []
    with engine.connect() as conn:
        for name, q in queries.items():
            t0 = time.perf_counter()
            df = pd.read_sql(text(q["sql"]), conn)
            ms = (time.perf_counter() - t0) * 1000
            results[name] = df
            timings.append({"query": name, "description": q["description"],
                            "rows": len(df), "time_ms": round(ms, 1)})
            df.to_csv(QUERY_DIR / f"{name}.csv", index=False, encoding="utf-8-sig")
            print(f"  {name:<36} {len(df):>4} sətir  {ms:7.1f} ms")
    return results, pd.DataFrame(timings)


# ----------------------------------------------------------------- qrafiklər
def fig_monthly(df):
    df = df.copy()
    df["month"] = pd.to_datetime(df["month"])
    fig, ax1 = plt.subplots(figsize=(11, 4.8))
    ax1.bar(df["month"], df["revenue"], width=20, color=PRIMARY, alpha=0.85, label="Gəlir")
    ax1.set_ylabel("Gəlir (AZN)")
    ax1.yaxis.set_major_formatter(azn)
    ax2 = ax1.twinx()
    ax2.plot(df["month"], df["orders_count"], color="#f59e0b", marker="o", lw=2, label="Sifariş sayı")
    ax2.set_ylabel("Sifariş sayı")
    ax2.grid(False)
    ax2.spines["top"].set_visible(False)
    ax1.set_title("Aylıq gəlir və sifariş sayı (2024–2025, çatdırılmış sifarişlər)")
    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax1.legend(h1 + h2, l1 + l2, loc="upper left", frameon=False)
    fig.savefig(FIGURES_DIR / "01_monthly_revenue.png")
    plt.close(fig)


def fig_category(df):
    df = df.sort_values("revenue")
    fig, ax = plt.subplots(figsize=(9, 5))
    bars = ax.barh(df["category_name"], df["revenue"], color=PRIMARY)
    for b, share in zip(bars, df["revenue_share_pct"]):
        ax.text(b.get_width(), b.get_y() + b.get_height() / 2, f"  {share:.1f}%",
                va="center", fontsize=9)
    ax.xaxis.set_major_formatter(azn)
    ax.set_xlabel("Gəlir (AZN)")
    ax.set_title("Kateqoriyalar üzrə gəlir və ümumi gəlirdəki pay")
    ax.grid(axis="y", visible=False)
    fig.savefig(FIGURES_DIR / "02_category_revenue.png")
    plt.close(fig)


def fig_payment(df):
    df = df.set_index("payment_method")[["completed", "failed", "refunded"]]
    fig, ax = plt.subplots(figsize=(9, 4.8))
    df.plot(kind="bar", stacked=True, ax=ax, color=["#16a34a", "#dc2626", "#f59e0b"], width=0.7)
    ax.set_xlabel("")
    ax.set_ylabel("Ödəniş sayı")
    ax.set_title("Ödəniş üsulları üzrə statuslar")
    ax.legend(["Uğurlu", "Uğursuz", "Geri qaytarılıb"], frameon=False)
    plt.xticks(rotation=0)
    fig.savefig(FIGURES_DIR / "03_payment_methods.png")
    plt.close(fig)


def fig_segments(df):
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    axes[0].bar(df["segment"], df["customers"], color=PALETTE[:len(df)])
    axes[0].set_title("Müştəri sayı")
    axes[1].bar(df["segment"], df["revenue_share_pct"], color=PALETTE[:len(df)])
    axes[1].set_title("Gəlirdəki pay (%)")
    for ax in axes:
        ax.tick_params(axis="x", rotation=15)
        ax.grid(axis="x", visible=False)
    fig.suptitle("RFM seqmentləri: müştəri sayı və gəlir payı")
    fig.savefig(FIGURES_DIR / "04_customer_segments.png")
    plt.close(fig)


def fig_yoy(df):
    p = df.pivot(index="category_name", columns="year", values="revenue").sort_values(2025)
    fig, ax = plt.subplots(figsize=(10, 5))
    y = np.arange(len(p))
    h = 0.38
    ax.barh(y - h / 2, p[2024], h, label="2024", color="#94a3b8")
    ax.barh(y + h / 2, p[2025], h, label="2025", color=PRIMARY)
    growth = df[df["year"] == 2025].set_index("category_name")["yoy_growth_pct"]
    for i, cat in enumerate(p.index):
        ax.text(p.loc[cat].max(), i, f"  +{growth[cat]:.1f}%", va="center", fontsize=9)
    ax.set_yticks(y, p.index)
    ax.xaxis.set_major_formatter(azn)
    ax.set_xlabel("Gəlir (AZN)")
    ax.set_title("Kateqoriyalar üzrə illik müqayisə (2024 və 2025)")
    ax.legend(frameon=False, loc="lower right")
    ax.grid(axis="y", visible=False)
    fig.savefig(FIGURES_DIR / "05_yoy_comparison.png")
    plt.close(fig)


def fig_order_distribution(engine):
    with engine.connect() as conn:
        amounts = pd.read_sql(text(
            "SELECT total_amount FROM orders WHERE status='delivered'"), conn)["total_amount"].to_numpy(float)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
    axes[0].hist(amounts, bins=60, color=PRIMARY, alpha=0.85)
    axes[0].axvline(np.mean(amounts), color="#dc2626", ls="--", label=f"Orta = {np.mean(amounts):.0f}")
    axes[0].axvline(np.median(amounts), color="#16a34a", ls="--", label=f"Median = {np.median(amounts):.0f}")
    axes[0].set_title("Xətti şkala")
    axes[0].legend(frameon=False)
    axes[1].hist(np.log10(amounts), bins=50, color="#7c3aed", alpha=0.85)
    axes[1].set_title("Loqarifmik şkala (log10)")
    for ax in axes:
        ax.set_ylabel("Sifariş sayı")
    axes[0].set_xlabel("Sifariş məbləği (AZN)")
    axes[1].set_xlabel("log10(məbləğ)")
    fig.suptitle("Sifariş məbləğlərinin paylanması")
    fig.savefig(FIGURES_DIR / "06_order_distribution.png")
    plt.close(fig)


def fig_city(df):
    city = df.groupby("shipping_city")["total_amount"].sum().sort_values()
    fig, ax = plt.subplots(figsize=(9, 4.8))
    ax.barh(city.index, city.values, color="#0891b2")
    ax.xaxis.set_major_formatter(azn)
    ax.set_xlabel("Uğurlu ödənişlərin məbləği (AZN)")
    ax.set_title("Şəhərlər üzrə satış (uğurlu ödənişlər)")
    ax.grid(axis="y", visible=False)
    fig.savefig(FIGURES_DIR / "07_city_sales.png")
    plt.close(fig)


# ----------------------------------------------------------------- hesabat
def write_markdown(r, timings, kpi):
    cat = r["q01_category_revenue"]
    seg = r["q05_top_customers_cte"]
    pay = r["q09_payment_methods"]
    m = r["q02_monthly_revenue"].copy()
    m["month"] = pd.to_datetime(m["month"])
    best = m.loc[m["revenue"].idxmax()]

    lines = [
        "# Satış hesabatı (avtomatik yaradılıb)", "",
        "## Əsas göstəricilər (KPI)", "",
        "| Göstərici | Dəyər |", "|---|---|",
        f"| Çatdırılmış sifariş sayı | {kpi['orders']:,} |",
        f"| Ümumi gəlir | {kpi['revenue']:,.2f} AZN |",
        f"| Orta çek (AOV) | {kpi['aov']:,.2f} AZN |",
        f"| Aktiv müştəri | {kpi['customers']:,} |",
        f"| Təkrar alış edən müştərilərin payı | {kpi['repeat_pct']:.1f}% |",
        f"| Ləğv + geri qaytarma nisbəti | {kpi['lost_pct']:.1f}% |",
        f"| Ən yüksək gəlirli ay | {best['month']:%Y-%m} ({best['revenue']:,.0f} AZN) |",
        "",
        "## Kateqoriyalar", "",
        cat.to_markdown(index=False), "",
        "## Müştəri seqmentləri", "",
        seg.to_markdown(index=False), "",
        "## Ödəniş üsulları", "",
        pay.to_markdown(index=False), "",
        "## Sorğuların icra müddəti", "",
        timings.to_markdown(index=False), "",
    ]
    (REPORTS_DIR / "sales_report.md").write_text("\n".join(lines), encoding="utf-8")


def compute_kpi(engine):
    sql = """
    WITH d AS (SELECT * FROM orders WHERE status = 'delivered'),
         per_c AS (SELECT customer_id, COUNT(*) n FROM d GROUP BY customer_id)
    SELECT (SELECT COUNT(*) FROM d)                                   AS orders,
           (SELECT SUM(total_amount) FROM d)                          AS revenue,
           (SELECT AVG(total_amount) FROM d)                          AS aov,
           (SELECT COUNT(*) FROM per_c)                               AS customers,
           (SELECT 100.0 * COUNT(*) FILTER (WHERE n > 1) / COUNT(*) FROM per_c) AS repeat_pct,
           (SELECT 100.0 * COUNT(*) FILTER (WHERE status IN ('cancelled','returned'))
                   / COUNT(*) FROM orders)                            AS lost_pct
    """
    with engine.connect() as conn:
        row = conn.execute(text(sql)).mappings().one()
    return {k: float(v) for k, v in row.items()}


def main():
    engine = create_engine(DATABASE_URL, future=True)
    queries = parse_queries(SQL_DIR / "02_analytics.sql")
    print(f"{len(queries)} analitik sorğu icra olunur:")
    r, timings = run_queries(engine, queries)
    kpi = compute_kpi(engine)

    print("\nQrafiklər qurulur...")
    fig_monthly(r["q02_monthly_revenue"])
    fig_category(r["q01_category_revenue"])
    fig_payment(r["q09_payment_methods"])
    fig_segments(r["q05_top_customers_cte"])
    fig_yoy(r["q08_yoy_growth_cte"])
    fig_order_distribution(engine)
    fig_city(r["q04_city_payment_having"])

    with pd.ExcelWriter(REPORTS_DIR / "sales_report.xlsx") as w:
        pd.DataFrame([kpi]).round(2).to_excel(w, sheet_name="KPI", index=False)
        timings.to_excel(w, sheet_name="Sorğu müddətləri", index=False)
        for name, df in r.items():
            df.to_excel(w, sheet_name=name[:31], index=False)
    write_markdown(r, timings, kpi)
    timings.to_csv(REPORTS_DIR / "query_timings.csv", index=False, encoding="utf-8-sig")

    print("\nKPI:", {k: round(v, 2) for k, v in kpi.items()})
    print("Hesabat:", REPORTS_DIR / "sales_report.xlsx")
    print("Qrafiklər:", FIGURES_DIR)


if __name__ == "__main__":
    main()
