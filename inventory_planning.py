"""Weekly inventory planning model for the Maggie / Mary / Lyn / Elsie stores.

Reads SKU-level weekly unit sales, forecasts demand, and produces the Monday
purchase-order recommendation.

Usage:
    python inventory_planning.py                      # forecast only, no stock data
    python inventory_planning.py --stock stock.csv    # full order recommendation
    python inventory_planning.py --marketing 1.30     # +30% expected demand

The stock file is a CSV with columns: sku, on_hand, incoming, moq, carton_multiple
Any column other than `sku` may be omitted or left blank.
"""

import argparse
import math

import pandas as pd

# SKUs beginning with this prefix are retired and excluded from every calculation.
EXCLUDED_SKU_PREFIX = "134821"

WEEK_COLUMNS = [
    "w29_2026_07_13",
    "w30_2026_07_20",
    "w31_2026_07_27",
    "w32_2026_08_03",
    "w33_2026_08_10_est",
]

# Service levels by ABC class. A items carry the highest cycle service because a
# stockout there costs the most revenue.
Z_BY_CLASS = {"A": 1.96, "B": 1.65, "C": 1.28}


def classify_trend(weeks: list[float]) -> tuple[str, float, float]:
    """Return (trend, week-over-week %, recent-half vs prior-half %).

    Two horizons are used together so that a single noisy week does not flip the
    classification: `wow` catches the turn, `half` confirms it is sustained.
    """
    w30, w31, w32, w33 = weeks[1], weeks[2], weeks[3], weeks[4]
    wow = (w33 / w32 - 1) * 100 if w32 else float("nan")
    prior, recent = w30 + w31, w32 + w33
    half = (recent / prior - 1) * 100 if prior else float("nan")

    mean = sum(weeks) / len(weeks)
    if mean > 0:
        sd = math.sqrt(sum((w - mean) ** 2 for w in weeks) / (len(weeks) - 1))
        cv = sd / mean
    else:
        cv = 0.0

    # A SKU whose swings dwarf its trend is called volatile rather than given a
    # direction the data cannot support.
    if cv > 0.55 and abs(half) < 60:
        return "Volatile", wow, half
    if half >= 12:
        return "Increasing", wow, half
    if half <= -12:
        return "Decreasing", wow, half
    return "Stable", wow, half


def base_forecast(weeks: list[float], trend: str) -> float:
    """Recency-weighted forecast for the next full week.

    A flat 4-week average lags a real turn by about two weeks. Weighting recent
    weeks more heavily lets the forecast follow demand instead of trailing it,
    and a declining SKU is weighted harder still so stock is not bought into a
    falling trend.
    """
    _, w30, w31, w32, w33 = weeks
    if trend == "Decreasing":
        return 0.55 * w33 + 0.30 * w32 + 0.15 * w31
    return 0.40 * w33 + 0.30 * w32 + 0.20 * w31 + 0.10 * w30


def confidence(weeks: list[float], cv: float) -> str:
    """Flag forecasts that rest on too little or too noisy a history."""
    if sum(weeks) < 60:
        return "Low - thin history"
    if cv > 0.55:
        return "Low - volatile"
    if cv > 0.35:
        return "Medium"
    return "High"


def risk_band(coverage_weeks: float, protection_weeks: float, has_stock: bool) -> str:
    """Rank a SKU by how likely it is to run out before the next delivery lands."""
    if not has_stock:
        return "- awaiting stock data"
    if coverage_weeks < protection_weeks * 0.5:
        return "Critical"
    if coverage_weeks < protection_weeks:
        return "High Risk"
    if coverage_weeks < protection_weeks * 1.5:
        return "Monitor"
    if coverage_weeks > protection_weeks * 3:
        return "Overstock Risk"
    return "Healthy"


def build_plan(
    sales: pd.DataFrame,
    stock: pd.DataFrame | None,
    lead_time_days: int,
    review_days: int,
    lead_time_sd_days: float,
    marketing_multiplier: float,
) -> pd.DataFrame:
    excluded = sales["sku"].str.startswith(EXCLUDED_SKU_PREFIX)
    if excluded.any():
        print(f"Excluded {excluded.sum()} SKUs starting {EXCLUDED_SKU_PREFIX}")
    sales = sales[~excluded].copy()

    protection_weeks = (lead_time_days + review_days) / 7
    records = []

    for row in sales.itertuples(index=False):
        weeks = [float(getattr(row, c)) for c in WEEK_COLUMNS]
        four_week = sum(weeks[:4])  # W29-W32, the last four complete weeks
        avg_weekly = four_week / 4

        trend, wow, half = classify_trend(weeks)
        mean = sum(weeks) / len(weeks)
        sd_weekly = (
            math.sqrt(sum((w - mean) ** 2 for w in weeks) / (len(weeks) - 1))
            if mean > 0
            else 0.0
        )
        cv = sd_weekly / mean if mean > 0 else 0.0

        base = base_forecast(weeks, trend)
        adjusted = base * marketing_multiplier

        records.append(
            {
                "sku": row.sku,
                "four_week_sales": four_week,
                "avg_weekly_sales": avg_weekly,
                "trend": trend,
                "wow_pct": wow,
                "half_vs_half_pct": half,
                "weekly_sd": sd_weekly,
                "cv": cv,
                "base_forecast": base,
                "adjusted_forecast": adjusted,
                "confidence": confidence(weeks, cv),
                **{c: weeks[i] for i, c in enumerate(WEEK_COLUMNS)},
            }
        )

    plan = pd.DataFrame(records).sort_values("four_week_sales", ascending=False)

    # ABC classification on share of 4-week units: A covers the first 80%,
    # B the next 15%, C the rest. Drives the service level each SKU is held to.
    total = plan["four_week_sales"].sum()
    cumulative = plan["four_week_sales"].cumsum() / total if total else plan["four_week_sales"] * 0
    plan["abc"] = pd.cut(
        cumulative, bins=[-0.01, 0.80, 0.95, 1.01], labels=["A", "B", "C"]
    ).astype(str)
    plan["z"] = plan["abc"].map(Z_BY_CLASS)

    # Safety stock covers two independent sources of error over the protection
    # interval: week-to-week demand variability, and variability in when the
    # supplier actually delivers.
    daily_demand = plan["adjusted_forecast"] / 7
    plan["safety_stock"] = (
        plan["z"]
        * (
            protection_weeks * plan["weekly_sd"] ** 2
            + (daily_demand**2) * (lead_time_sd_days**2)
        )
        ** 0.5
    ).round()

    # Cycle stock covers expected demand across the whole protection interval:
    # the wait for this order to land, plus the week until the next order goes in.
    plan["cycle_stock"] = (plan["adjusted_forecast"] * protection_weeks).round()
    plan["target_position"] = plan["cycle_stock"] + plan["safety_stock"]

    if stock is not None:
        plan = plan.merge(stock, on="sku", how="left")
    for col in ("on_hand", "incoming", "moq", "carton_multiple"):
        if col not in plan.columns:
            plan[col] = pd.NA

    has_stock = plan["on_hand"].notna()
    on_hand = plan["on_hand"].fillna(0)
    incoming = plan["incoming"].fillna(0)

    raw_order = (plan["target_position"] - on_hand - incoming).clip(lower=0)

    # Round up to the supplier's carton multiple, then lift to MOQ. Both are
    # skipped where the SKU has nothing to order.
    carton = plan["carton_multiple"].fillna(1).replace(0, 1)
    order = (raw_order / carton).apply(math.ceil) * carton
    moq = plan["moq"].fillna(0)
    order = order.where(order == 0, order.clip(lower=moq))

    plan["recommended_order_qty"] = order.astype(int)
    plan["stock_coverage_weeks"] = (
        (on_hand + incoming) / plan["adjusted_forecast"].replace(0, pd.NA)
    ).where(has_stock)
    plan["risk"] = [
        risk_band(cov, protection_weeks, hs)
        for cov, hs in zip(plan["stock_coverage_weeks"].fillna(0), has_stock)
    ]
    plan["order_qty_is_gross"] = ~has_stock

    return plan


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sales", default="data/weekly_sku_sales.csv")
    parser.add_argument("--stock", help="CSV of on_hand / incoming / moq / carton_multiple")
    parser.add_argument("--lead-time-days", type=int, default=7)
    parser.add_argument("--review-days", type=int, default=7)
    parser.add_argument("--lead-time-sd-days", type=float, default=2.0)
    parser.add_argument(
        "--marketing",
        type=float,
        default=1.0,
        help="Demand multiplier from the marketing scaling plan (1.30 = +30%%)",
    )
    parser.add_argument("--out", default="reports/monday_plan.csv")
    args = parser.parse_args()

    sales = pd.read_csv(args.sales)
    stock = pd.read_csv(args.stock) if args.stock else None

    if args.marketing == 1.0:
        print("Marketing scaling adjustment not provided - forecast is based on historical sales only.")

    plan = build_plan(
        sales,
        stock,
        args.lead_time_days,
        args.review_days,
        args.lead_time_sd_days,
        args.marketing,
    )
    plan.to_csv(args.out, index=False)

    label = "gross requirement (no stock data)" if stock is None else "net of stock on hand"
    print(f"{len(plan)} active SKUs -> {args.out}")
    print(f"Total recommended purchase ({label}): {plan['recommended_order_qty'].sum():,.0f} units")
    print(f"Next-week base forecast: {plan['base_forecast'].sum():,.0f} units")
    print(f"Marketing-adjusted forecast: {plan['adjusted_forecast'].sum():,.0f} units")


if __name__ == "__main__":
    main()
