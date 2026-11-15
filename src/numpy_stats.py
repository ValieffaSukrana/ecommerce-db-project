"""
NumPy ilə satış göstəricilərinin statistik təhlili.

Hesablanan göstəricilər: orta, median, standart kənarlaşma, dispersiya,
minimum, maksimum, kvartillər (Q1, Q3), IQR, variasiya əmsalı,
asimmetriya (skewness) və IQR üsulu ilə kənar dəyərlər (outliers).
"""
import numpy as np
import pandas as pd

from config import PROCESSED_DIR, REPORTS_DIR


def describe(values: np.ndarray, name: str) -> dict:
    v = np.asarray(values, dtype=float)
    v = v[~np.isnan(v)]
    mean = np.mean(v)
    std = np.std(v, ddof=1)
    q1, median, q3 = np.percentile(v, [25, 50, 75])
    iqr = q3 - q1
    low, high = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    skew = np.mean(((v - mean) / np.std(v)) ** 3)
    return {
        "göstərici": name,
        "say": v.size,
        "orta": round(mean, 2),
        "median": round(median, 2),
        "std": round(std, 2),
        "dispersiya": round(np.var(v, ddof=1), 2),
        "min": round(np.min(v), 2),
        "Q1": round(q1, 2),
        "Q3": round(q3, 2),
        "max": round(np.max(v), 2),
        "IQR": round(iqr, 2),
        "variasiya_əmsalı_%": round(std / mean * 100, 2),
        "asimmetriya": round(skew, 3),
        "kənar_dəyərlər": int(np.sum((v < low) | (v > high))),
    }


def main():
    orders = pd.read_parquet(PROCESSED_DIR / "orders.parquet")
    items = pd.read_parquet(PROCESSED_DIR / "order_items.parquet")
    products = pd.read_parquet(PROCESSED_DIR / "products.parquet")

    delivered = orders[orders["status"] == "delivered"]
    per_customer = delivered.groupby("customer_id")["total_amount"].sum().to_numpy()

    stats = pd.DataFrame([
        describe(orders["total_amount"].to_numpy(), "Sifariş məbləği (AZN)"),
        describe(delivered["total_amount"].to_numpy(), "Çatdırılmış sifariş məbləği (AZN)"),
        describe(items["quantity"].to_numpy(), "Sətir üzrə miqdar (ədəd)"),
        describe(items["line_total"].to_numpy(), "Sətir məbləği (AZN)"),
        describe(products["unit_price"].to_numpy(), "Məhsul qiyməti (AZN)"),
        describe(per_customer, "Müştəri üzrə ümumi xərc (AZN)"),
    ])

    # NumPy ilə əlavə: qiymət və miqdar arasında korrelyasiya
    corr = np.corrcoef(items["unit_price"].to_numpy(), items["quantity"].to_numpy())[0, 1]

    # Endirimin orta sətir məbləğinə təsiri (NumPy maskaları ilə)
    disc = items["discount"].to_numpy()
    lt = items["line_total"].to_numpy()
    disc_effect = pd.DataFrame({
        "endirim": np.unique(disc),
        "sətir_sayı": [int(np.sum(disc == d)) for d in np.unique(disc)],
        "orta_sətir_məbləği": [round(float(np.mean(lt[disc == d])), 2) for d in np.unique(disc)],
    })

    stats.to_csv(REPORTS_DIR / "numpy_statistics.csv", index=False, encoding="utf-8-sig")
    disc_effect.to_csv(REPORTS_DIR / "discount_effect.csv", index=False, encoding="utf-8-sig")

    pd.set_option("display.width", 200)
    pd.set_option("display.max_columns", 20)
    print("=== NumPy statistikası ===")
    print(stats.to_string(index=False))
    print(f"\nQiymət–miqdar korrelyasiyası (Pearson r): {corr:.3f}")
    print("\n=== Endirim səviyyəsi üzrə ===")
    print(disc_effect.to_string(index=False))


if __name__ == "__main__":
    main()
