"""
Pandas ilə qruplaşdırma və pivot cədvəllər (bazaya yükləmədən əvvəl ilkin təhlil).
"""
import pandas as pd

from config import PROCESSED_DIR, REPORTS_DIR


def load():
    t = {n: pd.read_parquet(PROCESSED_DIR / f"{n}.parquet")
         for n in ("categories", "customers", "products", "orders", "order_items")}
    sales = (t["order_items"]
             .merge(t["orders"][["order_id", "customer_id", "order_date", "status", "shipping_city"]],
                    on="order_id")
             .merge(t["products"][["product_id", "category_id", "brand"]], on="product_id")
             .merge(t["categories"], on="category_id"))
    sales["order_date"] = pd.to_datetime(sales["order_date"])
    sales["year"] = sales["order_date"].dt.year
    sales["quarter"] = sales["order_date"].dt.quarter
    return sales[sales["status"] == "delivered"]


def main():
    sales = load()

    by_category = (sales.groupby("category_name")
                   .agg(sifariş_sayı=("order_id", "nunique"),
                        satılan_ədəd=("quantity", "sum"),
                        gəlir=("line_total", "sum"),
                        orta_sətir=("line_total", "mean"))
                   .round(2).sort_values("gəlir", ascending=False))

    by_city = (sales.groupby("shipping_city")
               .agg(müştəri_sayı=("customer_id", "nunique"),
                    gəlir=("line_total", "sum"))
               .round(2).sort_values("gəlir", ascending=False))

    pivot_cat_year = pd.pivot_table(sales, values="line_total", index="category_name",
                                    columns="year", aggfunc="sum", margins=True,
                                    margins_name="Cəmi").round(2)

    pivot_city_quarter = pd.pivot_table(sales, values="line_total", index="shipping_city",
                                        columns=["year", "quarter"], aggfunc="sum",
                                        fill_value=0).round(0)

    with pd.ExcelWriter(REPORTS_DIR / "pandas_analysis.xlsx") as w:
        by_category.to_excel(w, sheet_name="Kateqoriya")
        by_city.to_excel(w, sheet_name="Şəhər")
        pivot_cat_year.to_excel(w, sheet_name="Pivot kateqoriya-il")
        pivot_city_quarter.to_excel(w, sheet_name="Pivot şəhər-rüb")

    pd.set_option("display.width", 200)
    print("=== Kateqoriya üzrə (groupby) ===\n", by_category, sep="")
    print("\n=== Şəhər üzrə (groupby) ===\n", by_city, sep="")
    print("\n=== Kateqoriya × il (pivot_table) ===\n", pivot_cat_year, sep="")


if __name__ == "__main__":
    main()
