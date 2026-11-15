"""ER diaqramının PNG şəklini yaradır (reports/figures/00_er_diagram.png)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

from config import FIGURES_DIR

TABLES = {
    "categories": (0.3, 7.6, ["PK  category_id", "      category_name (UQ)"]),
    "products": (0.3, 3.2, ["PK  product_id", "      product_name", "FK  category_id", "      brand",
                            "      unit_price", "      stock_quantity", "      created_at"]),
    "order_items": (5.0, 3.2, ["PK  order_item_id", "FK  order_id", "FK  product_id", "      quantity",
                               "      unit_price", "      discount", "      line_total"]),
    "orders": (5.0, 7.6, ["PK  order_id", "FK  customer_id", "      order_date", "      status",
                          "      shipping_city", "      total_amount"]),
    "customers": (9.7, 7.6, ["PK  customer_id", "      first_name", "      last_name", "      gender",
                             "      birth_date", "      email (UQ)", "      phone", "      city",
                             "      registration_date"]),
    "payments": (9.7, 3.2, ["PK  payment_id", "FK  order_id (UQ)", "      payment_date",
                            "      payment_method", "      amount", "      payment_status"]),
}
W, ROW, HEAD = 3.4, 0.36, 0.5


def box(ax, name, x, y, cols):
    h = HEAD + ROW * len(cols)
    ax.add_patch(FancyBboxPatch((x, y - h), W, h, boxstyle="round,pad=0.02",
                                fc="white", ec="#1e3a8a", lw=1.4))
    ax.add_patch(FancyBboxPatch((x, y - HEAD), W, HEAD, boxstyle="round,pad=0.02",
                                fc="#1e3a8a", ec="#1e3a8a", lw=1.4))
    ax.text(x + W / 2, y - HEAD / 2, name, ha="center", va="center",
            color="white", fontsize=11, fontweight="bold")
    for i, c in enumerate(cols):
        ax.text(x + 0.12, y - HEAD - ROW * (i + 0.5), c, va="center", fontsize=8.6,
                family="monospace", color="#b45309" if c.startswith(("PK", "FK")) else "#111827",
                fontweight="bold" if c.startswith("PK") else "normal")
    return {"l": x, "r": x + W, "t": y, "b": y - h, "cx": x + W / 2}


def link(ax, p1, p2, label):
    ax.annotate("", xy=p2, xytext=p1,
                arrowprops=dict(arrowstyle="-", color="#475569", lw=1.3))
    mx, my = (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2
    ax.text(mx, my, label, ha="center", va="center", fontsize=9, fontweight="bold",
            color="#dc2626", bbox=dict(fc="white", ec="none", pad=1.5))


def main():
    fig, ax = plt.subplots(figsize=(12, 8.2))
    b = {n: box(ax, n, *v) for n, v in TABLES.items()}
    link(ax, (b["categories"]["cx"], b["categories"]["b"]), (b["products"]["cx"], b["products"]["t"]), "1 : N")
    link(ax, (b["customers"]["l"], 7.0), (b["orders"]["r"], 7.0), "1 : N")
    link(ax, (b["orders"]["cx"], b["orders"]["b"]), (b["order_items"]["cx"], b["order_items"]["t"]), "1 : N")
    link(ax, (b["products"]["r"], 2.4), (b["order_items"]["l"], 2.4), "1 : N")
    # orders -> payments: cədvəllərin üstündən keçməsin deyə bucaqlı xətt
    y_mid = (b["customers"]["b"] + b["payments"]["t"]) / 2
    xs = [b["orders"]["r"] - 0.5, b["orders"]["r"] - 0.5, b["payments"]["cx"], b["payments"]["cx"]]
    ys = [b["orders"]["b"], y_mid, y_mid, b["payments"]["t"]]
    ax.plot(xs, ys, color="#475569", lw=1.3)
    ax.text((xs[1] + xs[2]) / 2, y_mid, "1 : 1", ha="center", va="center", fontsize=9,
            fontweight="bold", color="#dc2626", bbox=dict(fc="white", ec="none", pad=1.5))
    ax.set_xlim(0, 13.4)
    ax.set_ylim(-0.2, 8.0)
    ax.axis("off")
    fig.savefig(FIGURES_DIR / "00_er_diagram.png", dpi=170, bbox_inches="tight")
    plt.close(fig)
    print("ER diaqramı:", FIGURES_DIR / "00_er_diagram.png")


if __name__ == "__main__":
    main()
