"""
Təmizlənmiş məlumatların PostgreSQL bazasına yüklənməsi.

1. sql/01_schema.sql icra olunur (cədvəllər, PK/FK, CHECK, indekslər)
2. data/processed/*.parquet faylları FK asılılıq ardıcıllığı ilə yüklənir
3. Yükləmədən sonra sətir sayları və referensial bütövlük yoxlanılır
"""
import time

import pandas as pd
from sqlalchemy import create_engine, text

from config import DATABASE_URL, PROCESSED_DIR, SQL_DIR

# Valideyn cədvəllər övladlardan əvvəl yüklənməlidir (FK)
LOAD_ORDER = ["categories", "customers", "products", "orders", "order_items", "payments"]


def get_engine():
    return create_engine(DATABASE_URL, future=True)


def run_sql_file(engine, path):
    sql = path.read_text(encoding="utf-8")
    with engine.begin() as conn:
        conn.exec_driver_sql(sql)


def main():
    engine = get_engine()
    print("Sxem yaradılır:", SQL_DIR / "01_schema.sql")
    run_sql_file(engine, SQL_DIR / "01_schema.sql")

    for name in LOAD_ORDER:
        df = pd.read_parquet(PROCESSED_DIR / f"{name}.parquet")
        if "gender" in df.columns:
            df["gender"] = df["gender"].astype(str)
        t0 = time.perf_counter()
        df.to_sql(name, engine, if_exists="append", index=False,
                  method="multi", chunksize=2000)
        print(f"  {name:<12} {len(df):>6} sətir  ({time.perf_counter() - t0:.2f} s)")

    checks = {
        "Sətirləri olmayan sifariş": """
            SELECT COUNT(*) FROM orders o
            WHERE NOT EXISTS (SELECT 1 FROM order_items i WHERE i.order_id = o.order_id)""",
        "Ödənişi olmayan sifariş": """
            SELECT COUNT(*) FROM orders o
            WHERE NOT EXISTS (SELECT 1 FROM payments p WHERE p.order_id = o.order_id)""",
        "total_amount ≠ sətirlərin cəmi": """
            SELECT COUNT(*) FROM orders o
            JOIN (SELECT order_id, SUM(line_total) s FROM order_items GROUP BY order_id) t
              ON t.order_id = o.order_id
            WHERE ABS(o.total_amount - t.s) > 0.05""",
    }
    print("\nBütövlük yoxlanışı:")
    with engine.connect() as conn:
        for label, q in checks.items():
            print(f"  {label:<32}: {conn.execute(text(q)).scalar()}")
        total = sum(conn.execute(text(f"SELECT COUNT(*) FROM {t}")).scalar() for t in LOAD_ORDER)
    print(f"\nBazada cəmi qeyd: {total}")


if __name__ == "__main__":
    main()
