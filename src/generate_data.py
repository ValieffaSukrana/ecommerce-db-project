"""
Elektron ticarət üçün sintetik dataset generatoru.

Yaradılan cədvəllər və formatlar:
    categories.csv, customers.csv, orders.csv, order_items.csv  (CSV)
    products.json                                               (JSON)
    payments.xlsx                                               (Excel)

Real həyatdakı problemləri modelləşdirmək üçün məlumatlara qəsdən
boş dəyərlər, təkrarlanan sətirlər, formatı pozulmuş şəhər adları və
yanlış miqdarlar əlavə olunur (təmizləmə mərhələsində aradan qaldırılır).
"""
import json

import numpy as np
import pandas as pd

from config import RAW_DIR, RANDOM_SEED

rng = np.random.default_rng(RANDOM_SEED)

N_CUSTOMERS = 2000
N_PRODUCTS = 300
N_ORDERS = 8000
START_DATE = pd.Timestamp("2024-01-01")
END_DATE = pd.Timestamp("2025-12-31")

FIRST_NAMES_M = ["Əli", "Vüqar", "Rəşad", "Elvin", "Murad", "Tural", "Kamran", "Orxan",
                 "Nicat", "Fərid", "Samir", "Ramil", "Cavid", "Emil", "Ruslan", "Anar"]
FIRST_NAMES_F = ["Aysel", "Leyla", "Nigar", "Günay", "Aynur", "Səbinə", "Ülviyyə", "Nərmin",
                 "Fidan", "Lalə", "Şükranə", "Könül", "Aytən", "Zəhra", "Sevinc", "Gülnar"]
LAST_NAMES = ["Məmmədov", "Əliyev", "Həsənov", "Hüseynov", "Quliyev", "İsmayılov", "Abbasov",
              "Rzayev", "Kərimov", "Vəliyev", "Nəsirov", "Bağırov", "Cəfərov", "Mustafayev"]
CITIES = ["Bakı", "Gəncə", "Sumqayıt", "Mingəçevir", "Şəki", "Lənkəran", "Şirvan",
          "Naxçıvan", "Quba", "Qəbələ"]
CITY_WEIGHTS = np.array([0.45, 0.10, 0.10, 0.05, 0.05, 0.06, 0.04, 0.05, 0.05, 0.05])

CATEGORIES = {
    # ad: (orta qiymət AZN, brendlər)
    "Elektronika": (650, ["Samsung", "Apple", "Xiaomi", "Lenovo", "HP"]),
    "Məişət texnikası": (480, ["Bosch", "LG", "Beko", "Arçelik", "Philips"]),
    "Geyim": (55, ["Zara", "LC Waikiki", "Mango", "H&M", "Koton"]),
    "Ayaqqabı": (85, ["Nike", "Adidas", "Puma", "Skechers", "Ecco"]),
    "Kosmetika": (30, ["L'Oréal", "Nivea", "Garnier", "Maybelline", "Dove"]),
    "Kitab": (15, ["Qanun", "Alatoran", "TEAS Press", "Bakı Kitab", "Xan"]),
    "İdman": (70, ["Decathlon", "Nike", "Adidas", "Reebok", "Puma"]),
    "Oyuncaq": (35, ["LEGO", "Hasbro", "Mattel", "Playmobil", "Chicco"]),
    "Ev və bağ": (60, ["IKEA", "Tefal", "Karaca", "Paşabahçe", "Gardena"]),
    "Ərzaq": (12, ["Atena", "Milla", "Sevimli Dad", "Az-Granata", "Nestlé"]),
}
ORDER_STATUSES = ["delivered", "shipped", "processing", "cancelled", "returned"]
STATUS_WEIGHTS = [0.72, 0.08, 0.05, 0.10, 0.05]
PAYMENT_METHODS = ["card", "cash_on_delivery", "bank_transfer", "installment", "e_wallet"]
PAYMENT_WEIGHTS = [0.48, 0.22, 0.08, 0.14, 0.08]

TRANSLIT = str.maketrans({"ə": "e", "Ə": "E", "ü": "u", "Ü": "U", "ö": "o", "Ö": "O",
                          "ğ": "g", "Ğ": "G", "ı": "i", "İ": "I", "ş": "s", "Ş": "S",
                          "ç": "c", "Ç": "C"})


def random_dates(start, end, n, seasonal=False):
    """start-end aralığında n təsadüfi tarix; seasonal=True olduqda
    noyabr-dekabr aylarında sifariş sıxlığı artırılır."""
    days = (end - start).days + 1
    if not seasonal:
        offsets = rng.integers(0, days, n)
    else:
        all_days = pd.date_range(start, end, freq="D")
        weights = np.ones(len(all_days))
        weights[all_days.month.isin([11, 12])] *= 1.8   # bayram mövsümü
        weights[all_days.month.isin([3])] *= 1.3        # Novruz
        weights[all_days.day_of_week >= 5] *= 1.2         # həftəsonu
        # illik artım trendi
        weights *= np.linspace(1.0, 1.5, len(all_days))
        weights /= weights.sum()
        offsets = rng.choice(len(all_days), size=n, p=weights)
    seconds = rng.integers(8 * 3600, 23 * 3600, n)
    return start + pd.to_timedelta(offsets, unit="D") + pd.to_timedelta(seconds, unit="s")


def make_categories():
    return pd.DataFrame({
        "category_id": np.arange(1, len(CATEGORIES) + 1),
        "category_name": list(CATEGORIES.keys()),
    })


def make_customers():
    gender = rng.choice(["M", "F"], N_CUSTOMERS)
    first = np.where(gender == "M",
                     rng.choice(FIRST_NAMES_M, N_CUSTOMERS),
                     rng.choice(FIRST_NAMES_F, N_CUSTOMERS))
    last = rng.choice(LAST_NAMES, N_CUSTOMERS)
    last = np.where(gender == "F", np.char.add(last.astype(str), "a"), last)
    ids = np.arange(1, N_CUSTOMERS + 1)
    emails = [f"{f.translate(TRANSLIT).lower()}.{l.translate(TRANSLIT).lower()}{i}@mail.az"
              for f, l, i in zip(first, last, ids)]
    phones = [f"+99450{n:07d}" for n in rng.integers(0, 10**7, N_CUSTOMERS)]
    birth = random_dates(pd.Timestamp("1960-01-01"), pd.Timestamp("2006-12-31"), N_CUSTOMERS).date
    reg = random_dates(pd.Timestamp("2022-01-01"), pd.Timestamp("2025-06-30"), N_CUSTOMERS)

    df = pd.DataFrame({
        "customer_id": ids, "first_name": first, "last_name": last,
        "gender": gender, "birth_date": birth, "email": emails, "phone": phones,
        "city": rng.choice(CITIES, N_CUSTOMERS, p=CITY_WEIGHTS),
        "registration_date": reg.normalize(),
    })

    # --- Çirkli məlumat ---
    idx = rng.choice(N_CUSTOMERS, 60, replace=False)
    df.loc[idx[:30], "email"] = None                     # boş e-poçt
    df.loc[idx[30:], "phone"] = None                     # boş telefon
    idx = rng.choice(N_CUSTOMERS, 120, replace=False)
    df.loc[idx[:60], "city"] = df.loc[idx[:60], "city"].str.upper()        # BAKI
    df.loc[idx[60:], "city"] = "  " + df.loc[idx[60:], "city"] + " "       # boşluqlar
    dups = df.sample(40, random_state=RANDOM_SEED)                          # təkrar sətirlər
    return pd.concat([df, dups], ignore_index=True)


def make_products(categories):
    rows = []
    for pid in range(1, N_PRODUCTS + 1):
        cat_id = int(rng.integers(1, len(categories) + 1))
        cat_name = categories.loc[cat_id - 1, "category_name"]
        mean_price, brands = CATEGORIES[cat_name]
        brand = str(rng.choice(brands))
        price = float(np.round(rng.lognormal(np.log(mean_price), 0.45), 2))
        rows.append({
            "product_id": pid,
            "product_name": f"{brand} {cat_name} #{pid:03d}",
            "category_id": cat_id,
            "brand": brand,
            "unit_price": price,
            "stock_quantity": int(rng.integers(0, 500)),
            "created_at": str(random_dates(pd.Timestamp("2023-01-01"),
                                           pd.Timestamp("2024-06-30"), 1)[0].date()),
        })
    # Çirkli: bəzi məhsullarda qiymət boş
    for i in rng.choice(N_PRODUCTS, 6, replace=False):
        rows[i]["unit_price"] = None
    return rows


def make_orders(customers):
    real_customers = customers["customer_id"].unique()
    # Pareto: müştərilərin bir hissəsi daha aktivdir
    activity = np.minimum(rng.pareto(2.0, len(real_customers)) + 1, 12)
    activity /= activity.sum()
    cust = rng.choice(real_customers, N_ORDERS, p=activity)
    city_map = customers.drop_duplicates("customer_id").set_index("customer_id")["city"]

    df = pd.DataFrame({
        "order_id": np.arange(1, N_ORDERS + 1),
        "customer_id": cust,
        "order_date": random_dates(START_DATE, END_DATE, N_ORDERS, seasonal=True),
        "status": rng.choice(ORDER_STATUSES, N_ORDERS, p=STATUS_WEIGHTS),
    })
    df["shipping_city"] = df["customer_id"].map(city_map).str.strip().str.title()
    df = df.sort_values("order_date").reset_index(drop=True)
    df["order_id"] = np.arange(1, N_ORDERS + 1)
    dups = df.sample(25, random_state=1)
    return pd.concat([df, dups], ignore_index=True)


def make_order_items(orders, products):
    prices = {p["product_id"]: p["unit_price"] for p in products}
    # məhsul populyarlığı: bəzi məhsullar daha çox satılır
    popularity = rng.zipf(1.6, N_PRODUCTS).astype(float)
    popularity = np.minimum(popularity, 50)
    popularity /= popularity.sum()

    order_ids = orders["order_id"].unique()
    n_items = rng.choice([1, 2, 3, 4, 5], len(order_ids), p=[0.40, 0.28, 0.17, 0.10, 0.05])
    rows = []
    item_id = 1
    for oid, k in zip(order_ids, n_items):
        pids = rng.choice(np.arange(1, N_PRODUCTS + 1), k, replace=False, p=popularity)
        for pid in pids:
            base = prices[pid] if prices[pid] is not None else np.nan
            rows.append({
                "order_item_id": item_id, "order_id": int(oid), "product_id": int(pid),
                "quantity": int(rng.choice([1, 1, 1, 1, 2, 2, 3, 4])),
                "unit_price": base,
                "discount": float(rng.choice([0, 0, 0, 0.05, 0.10, 0.15, 0.20])),
            })
            item_id += 1
    df = pd.DataFrame(rows)
    # Çirkli: mənfi və sıfır miqdarlar, mövcud olmayan məhsul
    bad = rng.choice(len(df), 30, replace=False)
    df.loc[bad[:15], "quantity"] = -1
    df.loc[bad[15:25], "quantity"] = 0
    df.loc[bad[25:], "product_id"] = 9999
    return df


def make_payments(orders, items):
    o = orders.drop_duplicates("order_id").copy()
    it = items.copy()
    it["line"] = it["quantity"].clip(lower=0) * it["unit_price"] * (1 - it["discount"])
    totals = it.groupby("order_id")["line"].sum()
    o["amount"] = o["order_id"].map(totals).round(2)

    method = rng.choice(PAYMENT_METHODS, len(o), p=PAYMENT_WEIGHTS)
    status = np.where(o["status"].isin(["cancelled"]), "failed",
                      np.where(o["status"] == "returned", "refunded", "completed"))
    delay = pd.to_timedelta(rng.integers(0, 3 * 24 * 3600, len(o)), unit="s")
    df = pd.DataFrame({
        "payment_id": np.arange(1, len(o) + 1),
        "order_id": o["order_id"].values,
        "payment_date": (o["order_date"] + delay).values,
        "payment_method": method,
        "amount": o["amount"].values,
        "payment_status": status,
    })
    # Çirkli: bəzi ödəniş üsulları boş
    df.loc[rng.choice(len(df), 20, replace=False), "payment_method"] = None
    return df


def main():
    categories = make_categories()
    customers = make_customers()
    products = make_products(categories)
    orders = make_orders(customers)
    items = make_order_items(orders, products)
    payments = make_payments(orders, items)

    categories.to_csv(RAW_DIR / "categories.csv", index=False, encoding="utf-8")
    customers.to_csv(RAW_DIR / "customers.csv", index=False, encoding="utf-8")
    with open(RAW_DIR / "products.json", "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=2)
    orders.to_csv(RAW_DIR / "orders.csv", index=False, encoding="utf-8")
    items.to_csv(RAW_DIR / "order_items.csv", index=False, encoding="utf-8")
    payments.to_excel(RAW_DIR / "payments.xlsx", index=False)

    total = len(categories) + len(customers) + len(products) + len(orders) + len(items) + len(payments)
    print("Xam məlumatlar yaradıldı:", RAW_DIR)
    print(f"  categories : {len(categories):>6}")
    print(f"  customers  : {len(customers):>6}")
    print(f"  products   : {len(products):>6}")
    print(f"  orders     : {len(orders):>6}")
    print(f"  order_items: {len(items):>6}")
    print(f"  payments   : {len(payments):>6}")
    print(f"  CƏMİ       : {total:>6}")


if __name__ == "__main__":
    main()
