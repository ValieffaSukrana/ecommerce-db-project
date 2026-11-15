"""
Məlumatların yüklənməsi, keyfiyyət yoxlanışı və təmizlənməsi.

Giriş : data/raw/   (CSV, JSON, Excel)
Çıxış : data/processed/  (CSV və Parquet) + reports/data_quality_report.csv
"""
import numpy as np
import pandas as pd

from config import PROCESSED_DIR, RAW_DIR, REPORTS_DIR

CANONICAL_CITIES = ["Bakı", "Gəncə", "Sumqayıt", "Mingəçevir", "Şəki", "Lənkəran",
                    "Şirvan", "Naxçıvan", "Quba", "Qəbələ"]
_ASCII = str.maketrans({"ə": "e", "Ə": "e", "ü": "u", "Ü": "u", "ö": "o", "Ö": "o",
                        "ğ": "g", "Ğ": "g", "ı": "i", "I": "i", "İ": "i", "ş": "s",
                        "Ş": "s", "ç": "c", "Ç": "c"})


def _city_key(name: str) -> str:
    return name.strip().translate(_ASCII).lower()


CITY_LOOKUP = {_city_key(c): c for c in CANONICAL_CITIES}

quality_log = []


def log(table, check, before, after, note=""):
    quality_log.append({"table": table, "check": check, "before": before,
                        "after": after, "removed_or_fixed": before - after, "note": note})


def profile(df, name):
    """Cədvəlin qısa keyfiyyət profili: boş dəyərlər və təkrarlar."""
    nulls = df.isna().sum()
    print(f"\n[{name}] sətir={len(df)}, sütun={df.shape[1]}, "
          f"tam təkrar={df.duplicated().sum()}")
    if nulls.any():
        print("  boş dəyərlər:", nulls[nulls > 0].to_dict())


def load_raw():
    data = {
        "categories": pd.read_csv(RAW_DIR / "categories.csv"),
        "customers": pd.read_csv(RAW_DIR / "customers.csv"),
        "products": pd.read_json(RAW_DIR / "products.json"),
        "orders": pd.read_csv(RAW_DIR / "orders.csv"),
        "order_items": pd.read_csv(RAW_DIR / "order_items.csv"),
        "payments": pd.read_excel(RAW_DIR / "payments.xlsx"),
    }
    print("=== Xam məlumatların profili ===")
    for name, df in data.items():
        profile(df, name)
    return data


def normalize_city(series):
    return series.map(lambda v: CITY_LOOKUP.get(_city_key(v), v) if isinstance(v, str) else v)


def clean_customers(df):
    n = len(df)
    df = df.drop_duplicates()
    log("customers", "tam təkrar sətirlər", n, len(df))

    n = len(df)
    df = df.drop_duplicates(subset="customer_id", keep="first")
    log("customers", "təkrar customer_id", n, len(df))

    bad_city = (~df["city"].isin(CANONICAL_CITIES)).sum()
    df["city"] = normalize_city(df["city"])
    log("customers", "şəhər adlarının standartlaşdırılması", int(bad_city),
        int((~df["city"].isin(CANONICAL_CITIES)).sum()), "BAKI / boşluqlu adlar düzəldildi")

    for col in ("first_name", "last_name", "email", "phone"):
        df[col] = df[col].astype("string").str.strip()
    df["email"] = df["email"].str.lower()

    null_email = int(df["email"].isna().sum())
    null_phone = int(df["phone"].isna().sum())
    # Boş kontakt məlumatı müştərini silmək üçün səbəb deyil — NULL saxlanılır
    log("customers", "boş email (saxlanıldı, NULL)", null_email, null_email)
    log("customers", "boş telefon (saxlanıldı, NULL)", null_phone, null_phone)

    df["birth_date"] = pd.to_datetime(df["birth_date"]).dt.date
    df["registration_date"] = pd.to_datetime(df["registration_date"]).dt.date
    df["gender"] = df["gender"].astype("category")
    return df.sort_values("customer_id").reset_index(drop=True)


def clean_products(df, categories):
    n_null = int(df["unit_price"].isna().sum())
    # Boş qiymət — eyni kateqoriyanın median qiyməti ilə doldurulur
    df["unit_price"] = df.groupby("category_id")["unit_price"].transform(
        lambda s: s.fillna(np.round(s.median(), 2)))
    log("products", "boş unit_price (kateqoriya medianı ilə dolduruldu)",
        n_null, int(df["unit_price"].isna().sum()))

    n = len(df)
    df = df[df["category_id"].isin(categories["category_id"])]
    log("products", "mövcud olmayan kateqoriya", n, len(df))

    df["created_at"] = pd.to_datetime(df["created_at"]).dt.date
    df["unit_price"] = df["unit_price"].round(2)
    return df.reset_index(drop=True)


def clean_orders(df, customers):
    n = len(df)
    df = df.drop_duplicates()
    log("orders", "tam təkrar sətirlər", n, len(df))

    n = len(df)
    df = df[df["customer_id"].isin(customers["customer_id"])]
    log("orders", "mövcud olmayan müştəri (FK)", n, len(df))

    df["order_date"] = pd.to_datetime(df["order_date"])
    df["shipping_city"] = normalize_city(df["shipping_city"])
    return df.sort_values("order_id").reset_index(drop=True)


def clean_order_items(df, orders, products):
    n = len(df)
    df = df.drop_duplicates()
    log("order_items", "tam təkrar sətirlər", n, len(df))

    n = len(df)
    df = df[df["quantity"] > 0]
    log("order_items", "mənfi / sıfır miqdar", n, len(df))

    n = len(df)
    df = df[df["product_id"].isin(products["product_id"]) & df["order_id"].isin(orders["order_id"])]
    log("order_items", "mövcud olmayan məhsul / sifariş (FK)", n, len(df))

    # Boş vahid qiymət — məhsul kataloqundakı (artıq doldurulmuş) qiymətdən götürülür
    n_null = int(df["unit_price"].isna().sum())
    price_map = products.set_index("product_id")["unit_price"]
    df["unit_price"] = df["unit_price"].fillna(df["product_id"].map(price_map))
    log("order_items", "boş unit_price (kataloq qiyməti ilə)", n_null,
        int(df["unit_price"].isna().sum()))

    df["line_total"] = (df["quantity"] * df["unit_price"] * (1 - df["discount"])).round(2)
    return df.reset_index(drop=True)


def clean_payments(df, orders, items):
    n = len(df)
    df = df.drop_duplicates()
    log("payments", "tam təkrar sətirlər", n, len(df))

    n_null = int(df["payment_method"].isna().sum())
    df["payment_method"] = df["payment_method"].fillna("unknown")
    log("payments", "boş payment_method ('unknown')", n_null, 0)

    n = len(df)
    df = df[df["order_id"].isin(orders["order_id"])]
    log("payments", "mövcud olmayan sifariş (FK)", n, len(df))

    # Məbləğ təmizlənmiş sifariş sətirlərinə əsasən yenidən hesablanır
    totals = items.groupby("order_id")["line_total"].sum().round(2)
    new_amount = df["order_id"].map(totals).fillna(0)
    changed = int((~np.isclose(df["amount"].fillna(-1), new_amount)).sum())
    df["amount"] = new_amount
    log("payments", "məbləğ təmiz sətirlərdən yenidən hesablandı", changed, 0)

    df["payment_date"] = pd.to_datetime(df["payment_date"])
    return df.reset_index(drop=True)


def add_order_totals(orders, items):
    totals = items.groupby("order_id")["line_total"].sum().round(2)
    orders["total_amount"] = orders["order_id"].map(totals).fillna(0)
    n = len(orders)
    orders = orders[orders["total_amount"] > 0].reset_index(drop=True)
    log("orders", "sətirləri olmayan (boş) sifarişlər", n, len(orders))
    return orders


def save(tables):
    for name, df in tables.items():
        df.to_csv(PROCESSED_DIR / f"{name}.csv", index=False, encoding="utf-8")
        df.to_parquet(PROCESSED_DIR / f"{name}.parquet", index=False)
    pd.DataFrame(quality_log).to_csv(REPORTS_DIR / "data_quality_report.csv",
                                     index=False, encoding="utf-8-sig")


def main():
    raw = load_raw()
    categories = raw["categories"].drop_duplicates()
    customers = clean_customers(raw["customers"])
    products = clean_products(raw["products"], categories)
    orders = clean_orders(raw["orders"], customers)
    items = clean_order_items(raw["order_items"], orders, products)
    orders = add_order_totals(orders, items)
    items = items[items["order_id"].isin(orders["order_id"])].reset_index(drop=True)
    payments = clean_payments(raw["payments"], orders, items)

    tables = {"categories": categories, "customers": customers, "products": products,
              "orders": orders, "order_items": items, "payments": payments}
    save(tables)

    print("\n=== Təmizləmə jurnalı ===")
    print(pd.DataFrame(quality_log).to_string(index=False))
    print("\n=== Təmiz cədvəllər ===")
    for name, df in tables.items():
        print(f"  {name:<12}: {len(df):>6}")
    print(f"  CƏMİ        : {sum(len(d) for d in tables.values()):>6}")
    print("Saxlanıldı:", PROCESSED_DIR)


if __name__ == "__main__":
    main()
