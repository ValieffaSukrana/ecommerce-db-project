"""
Bütün layihəni ardıcıl icra edir:
    1. Dataset generasiyası      (src/generate_data.py)
    2. Təmizləmə və ilkin emal   (src/clean_data.py)
    3. NumPy statistikası        (src/numpy_stats.py)
    4. Pandas groupby / pivot    (src/pandas_analysis.py)
    5. PostgreSQL-ə yükləmə      (src/load_to_db.py)
    6. SQL təhlili və hesabat    (src/sales_report.py)

İstifadə:
    python run_pipeline.py            # hamısı
    python run_pipeline.py --no-db    # yalnız 1–4 (baza olmadan)
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

import clean_data  # noqa: E402
import generate_data  # noqa: E402
import numpy_stats  # noqa: E402
import pandas_analysis  # noqa: E402

STEPS = [
    ("Dataset generasiyası", generate_data.main),
    ("Təmizləmə və ilkin emal", clean_data.main),
    ("NumPy statistikası", numpy_stats.main),
    ("Pandas groupby / pivot_table", pandas_analysis.main),
]

if "--no-db" not in sys.argv:
    import load_to_db  # noqa: E402
    import sales_report  # noqa: E402
    STEPS += [
        ("PostgreSQL-ə yükləmə", load_to_db.main),
        ("SQL təhlili, qrafiklər və hesabat", sales_report.main),
    ]

if __name__ == "__main__":
    t_all = time.perf_counter()
    for i, (title, fn) in enumerate(STEPS, 1):
        print(f"\n{'=' * 70}\n[{i}/{len(STEPS)}] {title}\n{'=' * 70}")
        t0 = time.perf_counter()
        fn()
        print(f"--> {time.perf_counter() - t0:.1f} s")
    print(f"\nHazırdır. Ümumi müddət: {time.perf_counter() - t_all:.1f} s")
