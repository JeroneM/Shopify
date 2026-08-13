# Inventory Plan — week commencing 2026-08-17

**Run date:** 2026-08-13 (Thursday) · **Data source:** `Maggies Tank_COE` Google Sheet, last synced 2026-08-13 15:12
**Stores:** Maggie, Mary, Lyn, Elsie · **Excluded:** all SKUs beginning `134821`

> **This is a demand plan, not a signed-off purchase order.** No current-stock, inbound-PO or
> marketing-scaling data exists in the source sheet. The `Target Position` column is the gross
> inventory position each SKU should reach. Net order quantity = Target Position − on hand −
> confirmed incoming, and cannot be computed until that data is supplied.

## Headline

| | |
|---|---|
| Active SKUs planned | 81 |
| 4-week units (W29–W32, Jul 13 – Aug 9) | 126,979 |
| Next full week base forecast | 32,579 |
| Marketing-adjusted forecast | 32,579 (multiplier 1.00 — no plan provided) |
| Cycle stock (2-week protection interval) | 65,158 |
| Safety stock | 33,049 |
| **Target inventory position** | **98,207** |

## 1. What the demand is actually doing

Total demand peaked in W31 (Jul 27 – Aug 2) at 40,465 units and has fallen for two consecutive
weeks: W32 34,352, W33 estimated 31,161 (−9.3% week over week).

Read on its own that looks like a business cooling off. It is not. The aggregate decline hides a
violent shift in the size curve, and the two halves of the range are moving in opposite directions.

### QL1058 by size — the single most important pattern

| Size | W29 | W30 | W31 | W32 | W33 (est) | WoW | Recent 2wk vs prior 2wk |
|---|---|---|---|---|---|---|---|
| S | 1,593 | 2,007 | 2,654 | 1,440 | 618 | −57% | **−56%** |
| M | 3,535 | 5,662 | 7,532 | 4,191 | 2,189 | −48% | **−52%** |
| L | 4,283 | 6,645 | 8,931 | 5,652 | 3,911 | −31% | **−39%** |
| XL | 5,648 | 8,135 | 10,567 | 11,212 | 11,999 | +7% | **+24%** |
| 2XL | 3,363 | 4,989 | 6,505 | 6,188 | 6,283 | +2% | **+8%** |
| 3XL | 2,334 | 3,187 | 3,634 | 5,116 | 5,688 | +11% | **+58%** |

Every colourway is down 3–16% over the same window, and they are down by roughly the same amount.
Colour mix is stable; **size mix is not**. Buying to the aggregate trend would under-buy XL/3XL and
badly over-buy S/M.

Treat the S/M collapse with care. It is steep, consistent across all eight colourways, and began the
same week XL/3XL accelerated — which is the signature of a genuine mix shift rather than a data
artefact. But a stockout in the small sizes would look identical in this data, and no inventory
history was supplied to rule it out. **Confirm S/M availability before cutting those orders.**

## 2. Method

| Step | Approach |
|---|---|
| Weeks | Monday–Sunday. W33 (from 2026-08-10) is incomplete and carries a full-week estimate. |
| Base forecast | Recency-weighted: 40% W33e + 30% W32 + 20% W31 + 10% W30. Declining SKUs use 55/30/15 across W33e/W32/W31 so the forecast follows the fall rather than trailing it. |
| Trend | Week-over-week plus recent-two-weeks vs prior-two-weeks, so one noisy week cannot flip the call. A SKU whose swings dwarf its trend is labelled Volatile. |
| Protection interval | Supplier lead time (7 days) + review period (7 days) = 2 weeks. |
| Cycle stock | Marketing-adjusted forecast × 2 weeks. |
| Safety stock | `z × √(protection_weeks × σ_weekly² + daily_demand² × σ_leadtime²)`. SKU-specific: driven by that SKU's own weekly volatility, so a steady seller carries far less buffer than a spiky one. |
| Service level | ABC by share of 4-week units — A (first 80%) z=1.96, B (next 15%) z=1.65, C (remainder) z=1.28. |
| Order quantity | `max(0, Target Position − on hand − confirmed incoming)`, then rounded up to carton multiple and lifted to MOQ. Never negative. |

Reproduce with `python inventory_planning.py --stock stock.csv --marketing 1.30`.

## 3. Monday purchase plan — by SKU

| SKU | Product | 4-Wk Sales | Avg Wk | Trend | Base Fcst | Mkt-Adj Fcst | Stock | Incoming | Cycle | Safety | Target Position | Coverage | Risk |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| QL1058-nude-XL | Built-in Bra Comfort Tank - Nude / XL | 13,106 | 3,276 | Increasing | 4,014 | 4,014 | — | — | 8,028 | 3,326 | 11,354 | — | ⚪ pending stock |
| QL1058-nude-L | Built-in Bra Comfort Tank - Nude / L | 9,092 | 2,273 | Decreasing | 1,794 | 1,794 | — | — | 3,587 | 2,189 | 5,776 | — | ⚪ pending stock |
| QL1058-nude-2XL | Built-in Bra Comfort Tank - Nude / 2XL | 7,693 | 1,923 | Stable | 2,208 | 2,208 | — | — | 4,415 | 1,757 | 6,172 | — | ⚪ pending stock |
| QL1058-black-XL | Built-in Bra Comfort Tank - Black / XL | 7,329 | 1,832 | Increasing | 2,312 | 2,312 | — | — | 4,625 | 2,022 | 6,647 | — | ⚪ pending stock |
| QL1058-nude-M | Built-in Bra Comfort Tank - Nude / M | 7,299 | 1,825 | Decreasing | 1,250 | 1,250 | — | — | 2,500 | 2,059 | 4,559 | — | ⚪ pending stock |
| QL1058-white-XL | Built-in Bra Comfort Tank - White / XL | 6,474 | 1,618 | Increasing | 2,072 | 2,072 | — | — | 4,143 | 1,849 | 5,992 | — | ⚪ pending stock |
| QL1058-nude-3XL | Built-in Bra Comfort Tank - Nude / 3XL | 5,584 | 1,396 | Increasing | 1,898 | 1,898 | — | — | 3,796 | 1,823 | 5,619 | — | ⚪ pending stock |
| QL1058-black-L | Built-in Bra Comfort Tank - Black / L | 5,421 | 1,355 | Decreasing | 1,094 | 1,094 | — | — | 2,189 | 1,298 | 3,487 | — | ⚪ pending stock |
| QL1058-white-L | Built-in Bra Comfort Tank - White / L | 4,723 | 1,181 | Decreasing | 960 | 960 | — | — | 1,920 | 1,279 | 3,199 | — | ⚪ pending stock |
| QL1058-black-2XL | Built-in Bra Comfort Tank - Black / 2XL | 4,537 | 1,134 | Increasing | 1,362 | 1,362 | — | — | 2,725 | 1,132 | 3,857 | — | ⚪ pending stock |
| QL1058-black-M | Built-in Bra Comfort Tank - Black / M | 4,403 | 1,101 | Decreasing | 749 | 749 | — | — | 1,497 | 1,297 | 2,794 | — | ⚪ pending stock |
| QL1058-white-M | Built-in Bra Comfort Tank - White / M | 4,108 | 1,027 | Decreasing | 709 | 709 | — | — | 1,419 | 1,223 | 2,642 | — | ⚪ pending stock |
| QL1058-white-2XL | Built-in Bra Comfort Tank - White / 2XL | 3,581 | 895 | Stable | 1,058 | 1,058 | — | — | 2,117 | 904 | 3,021 | — | ⚪ pending stock |
| QL1058-black-3XL | Built-in Bra Comfort Tank - Black / 3XL | 2,991 | 748 | Increasing | 1,024 | 1,024 | — | — | 2,048 | 1,005 | 3,053 | — | ⚪ pending stock |
| QL1058-nude-S | Built-in Bra Comfort Tank - Nude / S | 2,521 | 630 | Decreasing | 380 | 380 | — | — | 760 | 683 | 1,443 | — | ⚪ pending stock |
| QL1058-white-3XL | Built-in Bra Comfort Tank - White / 3XL | 2,353 | 588 | Increasing | 793 | 793 | — | — | 1,586 | 753 | 2,339 | — | ⚪ pending stock |
| QL1058-coffee-XL | Built-in Bra Comfort Tank - Coffee / XL | 2,335 | 584 | Increasing | 719 | 719 | — | — | 1,438 | 631 | 2,069 | — | ⚪ pending stock |
| QL1058-grey-XL | Built-in Bra Comfort Tank - Grey / XL | 1,981 | 495 | Increasing | 631 | 631 | — | — | 1,262 | 573 | 1,835 | — | ⚪ pending stock |
| QL1058-red-XL | Built-in Bra Comfort Tank - Red / XL | 1,812 | 453 | Increasing | 562 | 562 | — | — | 1,123 | 478 | 1,601 | — | ⚪ pending stock |
| QL1058-coffee-L | Built-in Bra Comfort Tank - Coffee / L | 1,712 | 428 | Decreasing | 355 | 355 | — | — | 710 | 439 | 1,149 | — | ⚪ pending stock |
| QL1058-green-XL | Built-in Bra Comfort Tank - Green / XL | 1,673 | 418 | Increasing | 514 | 514 | — | — | 1,027 | 421 | 1,448 | — | ⚪ pending stock |
| QL1058-black-S | Built-in Bra Comfort Tank - Black / S | 1,641 | 410 | Decreasing | 249 | 249 | — | — | 499 | 392 | 891 | — | ⚪ pending stock |
| QL1058-white-S | Built-in Bra Comfort Tank - White / S | 1,596 | 399 | Decreasing | 244 | 244 | — | — | 487 | 416 | 903 | — | ⚪ pending stock |
| QL1058-coffee-M | Built-in Bra Comfort Tank - Coffee / M | 1,431 | 358 | Decreasing | 259 | 259 | — | — | 518 | 339 | 857 | — | ⚪ pending stock |
| QL1058-coffee-2XL | Built-in Bra Comfort Tank - Coffee / 2XL | 1,416 | 354 | Increasing | 427 | 427 | — | — | 854 | 305 | 1,159 | — | ⚪ pending stock |
| QL1058-grey-L | Built-in Bra Comfort Tank - Grey / L | 1,365 | 341 | Decreasing | 292 | 292 | — | — | 583 | 277 | 860 | — | ⚪ pending stock |
| QL1058-red-L | Built-in Bra Comfort Tank - Red / L | 1,309 | 327 | Decreasing | 278 | 278 | — | — | 556 | 274 | 830 | — | ⚪ pending stock |
| QL1058-green-L | Built-in Bra Comfort Tank - Green / L | 1,294 | 324 | Decreasing | 284 | 284 | — | — | 568 | 283 | 851 | — | ⚪ pending stock |
| QL1058-grey-2XL | Built-in Bra Comfort Tank - Grey / 2XL | 1,199 | 300 | Stable | 348 | 348 | — | — | 697 | 240 | 937 | — | ⚪ pending stock |
| QL1058-red-2XL | Built-in Bra Comfort Tank - Red / 2XL | 1,092 | 273 | Stable | 324 | 324 | — | — | 649 | 226 | 875 | — | ⚪ pending stock |
| QL1058-grey-M | Built-in Bra Comfort Tank - Grey / M | 1,073 | 268 | Decreasing | 174 | 174 | — | — | 348 | 281 | 629 | — | ⚪ pending stock |
| QL1058-green-M | Built-in Bra Comfort Tank - Green / M | 1,059 | 265 | Decreasing | 175 | 175 | — | — | 350 | 248 | 598 | — | ⚪ pending stock |
| QL1058-red-M | Built-in Bra Comfort Tank - Red / M | 1,038 | 260 | Decreasing | 179 | 179 | — | — | 357 | 235 | 592 | — | ⚪ pending stock |
| QL1058-green-2XL | Built-in Bra Comfort Tank - Green / 2XL | 1,001 | 250 | Increasing | 285 | 285 | — | — | 570 | 174 | 744 | — | ⚪ pending stock |
| QL1058-beanpaste-XL | Built-in Bra Comfort Tank - Beanpaste / XL | 852 | 213 | Increasing | 267 | 267 | — | — | 534 | 196 | 730 | — | ⚪ pending stock |
| QL1058-grey-3XL | Built-in Bra Comfort Tank - Grey / 3XL | 841 | 210 | Increasing | 272 | 272 | — | — | 543 | 208 | 751 | — | ⚪ pending stock |
| QL1058-red-3XL | Built-in Bra Comfort Tank - Red / 3XL | 786 | 196 | Increasing | 275 | 275 | — | — | 550 | 236 | 786 | — | ⚪ pending stock |
| QL1058-coffee-3XL | Built-in Bra Comfort Tank - Coffee / 3XL | 766 | 192 | Increasing | 275 | 275 | — | — | 551 | 258 | 809 | — | ⚪ pending stock |
| QL1058-green-3XL | Built-in Bra Comfort Tank - Green / 3XL | 621 | 155 | Increasing | 206 | 206 | — | — | 411 | 124 | 535 | — | ⚪ pending stock |
| QL1058-beanpaste-L | Built-in Bra Comfort Tank - Beanpaste / L | 595 | 149 | Decreasing | 130 | 130 | — | — | 260 | 99 | 359 | — | ⚪ pending stock |
| QL1058-coffee-S | Built-in Bra Comfort Tank - Coffee / S | 546 | 136 | Decreasing | 84 | 84 | — | — | 169 | 101 | 270 | — | ⚪ pending stock |
| QL1058-beanpaste-2XL | Built-in Bra Comfort Tank - Beanpaste / 2XL | 526 | 132 | Stable | 156 | 156 | — | — | 312 | 84 | 396 | — | ⚪ pending stock |
| QL1058-beanpaste-M | Built-in Bra Comfort Tank - Beanpaste / M | 509 | 127 | Decreasing | 96 | 96 | — | — | 193 | 109 | 302 | — | ⚪ pending stock |
| QL1058-grey-S | Built-in Bra Comfort Tank - Grey / S | 409 | 102 | Decreasing | 56 | 56 | — | — | 111 | 78 | 189 | — | ⚪ pending stock |
| QL1058-green-S | Built-in Bra Comfort Tank - Green / S | 400 | 100 | Decreasing | 65 | 65 | — | — | 130 | 77 | 207 | — | ⚪ pending stock |
| QL1058-red-S | Built-in Bra Comfort Tank - Red / S | 382 | 96 | Decreasing | 55 | 55 | — | — | 110 | 73 | 183 | — | ⚪ pending stock |
| QL1058-beanpaste-3XL | Built-in Bra Comfort Tank - Beanpaste / 3XL | 329 | 82 | Increasing | 113 | 113 | — | — | 226 | 73 | 299 | — | ⚪ pending stock |
| QL1058-beanpaste-S | Built-in Bra Comfort Tank - Beanpaste / S | 199 | 50 | Decreasing | 37 | 37 | — | — | 73 | 33 | 106 | — | ⚪ pending stock |
| QA1114-black-xl | Ribbed Cotton Built-in Bra Tank - Black / XL | 168 | 42 | Increasing | 50 | 50 | — | — | 100 | 35 | 135 | — | ⚪ pending stock |
| QA1114-black-l | Ribbed Cotton Built-in Bra Tank - Black / L | 123 | 31 | Decreasing | 26 | 26 | — | — | 52 | 24 | 76 | — | ⚪ pending stock |
| QA1114-black-2xl | Ribbed Cotton Built-in Bra Tank - Black / 2XL | 112 | 28 | Stable | 34 | 34 | — | — | 67 | 19 | 86 | — | ⚪ pending stock |
| QA1114-white-xl | Ribbed Cotton Built-in Bra Tank - White / XL | 100 | 25 | Increasing | 33 | 33 | — | — | 65 | 20 | 85 | — | ⚪ pending stock |
| QA1114-white-l | Ribbed Cotton Built-in Bra Tank - White / L | 97 | 24 | Decreasing | 18 | 18 | — | — | 36 | 13 | 49 | — | ⚪ pending stock |
| QA1114-white-2xl | Ribbed Cotton Built-in Bra Tank - White / 2XL | 84 | 21 | Stable | 26 | 26 | — | — | 53 | 16 | 69 | — | ⚪ pending stock |
| QA1114-yellow-s | Ribbed Cotton Built-in Bra Tank - Yellow / S | 84 | 21 | Volatile | 24 | 24 | — | — | 47 | 24 | 71 | — | ⚪ pending stock |
| QA1114-black-m | Ribbed Cotton Built-in Bra Tank - Black / M | 82 | 20 | Decreasing | 13 | 13 | — | — | 25 | 22 | 47 | — | ⚪ pending stock |
| QL1046-6pcs | Mystery Gift (bundle) | 78 | 20 | Volatile | 23 | 23 | — | — | 46 | 23 | 69 | — | ⚪ pending stock |
| QA1114-black-3xl | Ribbed Cotton Built-in Bra Tank - Black / 3XL | 73 | 18 | Increasing | 21 | 21 | — | — | 42 | 10 | 52 | — | ⚪ pending stock |
| QA1114-white-m | Ribbed Cotton Built-in Bra Tank - White / M | 65 | 16 | Volatile | 11 | 11 | — | — | 22 | 17 | 39 | — | ⚪ pending stock |
| QL1047-BLK-2XL | Ribbed Cotton LS Sculpt Top - BLK / 2XL | 62 | 16 | Volatile | 22 | 22 | — | — | 43 | 20 | 63 | — | ⚪ pending stock |
| QA1114-white-3xl | Ribbed Cotton Built-in Bra Tank - White / 3XL | 58 | 14 | Increasing | 14 | 14 | — | — | 29 | 8 | 37 | — | ⚪ pending stock |
| QA1114-khaki-xl | Ribbed Cotton Built-in Bra Tank - Khaki / XL | 55 | 14 | Decreasing | 9 | 9 | — | — | 18 | 11 | 29 | — | ⚪ pending stock |
| QL1047-BLK-M | Ribbed Cotton LS Sculpt Top - BLK / M | 52 | 13 | Volatile | 16 | 16 | — | — | 33 | 19 | 52 | — | ⚪ pending stock |
| QA1114-pink-l | Ribbed Cotton Built-in Bra Tank - Pink / L | 48 | 12 | Volatile | 10 | 10 | — | — | 20 | 12 | 32 | — | ⚪ pending stock |
| QL1047-BLK-XL | Ribbed Cotton LS Sculpt Top - BLK / XL | 47 | 12 | Increasing | 27 | 27 | — | — | 54 | 30 | 84 | — | ⚪ pending stock |
| QL1047-BLK-L | Ribbed Cotton LS Sculpt Top - BLK / L | 47 | 12 | Volatile | 16 | 16 | — | — | 31 | 21 | 52 | — | ⚪ pending stock |
| QA1114-yellow-xl | Ribbed Cotton Built-in Bra Tank - Yellow / XL | 46 | 12 | Decreasing | 13 | 13 | — | — | 26 | 8 | 34 | — | ⚪ pending stock |
| QA1114-pink-xl | Ribbed Cotton Built-in Bra Tank - Pink / XL | 46 | 12 | Increasing | 14 | 14 | — | — | 27 | 6 | 33 | — | ⚪ pending stock |
| QA1114-yellow-2xl | Ribbed Cotton Built-in Bra Tank - Yellow / 2XL | 43 | 11 | Increasing | 12 | 12 | — | — | 24 | 6 | 30 | — | ⚪ pending stock |
| QA1114-yellow-l | Ribbed Cotton Built-in Bra Tank - Yellow / L | 42 | 10 | Decreasing | 7 | 7 | — | — | 15 | 12 | 27 | — | ⚪ pending stock |
| QA1114-pink-2xl | Ribbed Cotton Built-in Bra Tank - Pink / 2XL | 42 | 10 | Increasing | 15 | 15 | — | — | 30 | 10 | 40 | — | ⚪ pending stock |
| QA1114-khaki-l | Ribbed Cotton Built-in Bra Tank - Khaki / L | 40 | 10 | Decreasing | 7 | 7 | — | — | 13 | 5 | 18 | — | ⚪ pending stock |
| QA1114-khaki-2xl | Ribbed Cotton Built-in Bra Tank - Khaki / 2XL | 38 | 10 | Increasing | 11 | 11 | — | — | 22 | 6 | 28 | — | ⚪ pending stock |
| QA1114-pink-m | Ribbed Cotton Built-in Bra Tank - Pink / M | 36 | 9 | Stable | 7 | 7 | — | — | 15 | 5 | 20 | — | ⚪ pending stock |
| QA1114-black-s | Ribbed Cotton Built-in Bra Tank - Black / S | 35 | 9 | Decreasing | 5 | 5 | — | — | 11 | 7 | 18 | — | ⚪ pending stock |
| QA1114-pink-3xl | Ribbed Cotton Built-in Bra Tank - Pink / 3XL | 32 | 8 | Decreasing | 6 | 6 | — | — | 12 | 5 | 17 | — | ⚪ pending stock |
| QA1114-yellow-m | Ribbed Cotton Built-in Bra Tank - Yellow / M | 29 | 7 | Decreasing | 6 | 6 | — | — | 12 | 6 | 18 | — | ⚪ pending stock |
| QL1047-black-x | Ribbed Cotton LS Sculpt Top - BLACK / X | 29 | 7 | Decreasing | 0 | 0 | — | — | 0 | 18 | 18 | — | ⚪ pending stock |
| QL1047-GRY-M | Ribbed Cotton LS Sculpt Top - GRY / M | 28 | 7 | Volatile | 7 | 7 | — | — | 15 | 12 | 27 | — | ⚪ pending stock |
| QA1114-gray-m | Ribbed Cotton Built-in Bra Tank - Gray / M | 28 | 7 | Decreasing | 5 | 5 | — | — | 9 | 8 | 17 | — | ⚪ pending stock |
| QL1047-BLK-S | Ribbed Cotton LS Sculpt Top - BLK / S | 27 | 7 | Volatile | 10 | 10 | — | — | 20 | 11 | 31 | — | ⚪ pending stock |

## 4. Executive summary

**Total recommended purchase** — 98,207 units gross. This is the target inventory position across
81 active SKUs, not a net order. Every unit already on hand or on an open PO comes straight off it.

**Fastest growing** — the entire 3XL range. QL1058 coffee 3XL +84%, red 3XL +67%, black 3XL +65%,
beanpaste 3XL +57%, nude 3XL +55%, white 3XL +54% (recent two weeks vs prior two). XL is close
behind at +24% overall. These are the SKUs most likely to stock out before the next delivery lands.

**Declining** — the entire S and M range, without exception. QL1058 grey S −59%, white S −57%,
red S −56%, black S −56%, nude S −56%, and the M sizes −48 to −52%. L is down 39% and is following
the same path one step behind.

**Critical SKUs** — cannot be ranked without stock data. On demand alone the exposure sits with
QL1058 nude XL (4,014/wk forecast, 11,354 target), black XL (2,312), nude 2XL (2,208), white XL
(2,072) and nude 3XL (1,898). Those five carry 38% of next week's forecast.

**Potential overstock** — QL1058 nude M, black M, white M, nude S, black S and white S. Combined
4-week sales of 21,568 units against a combined forecast of 3,581 for next week. If stock was bought
against the July run rate, there is likely a large excess sitting in these six.

**Marketing impact** — *Marketing scaling adjustment not provided — forecast is based on historical
sales only.* The multiplier is set to 1.00. There is no ad-spend history anywhere in the source, so
the spend-to-units relationship cannot be estimated: a stated +30% spend must not be assumed to mean
+30% units until we have the data to fit it. Supply a multiplier and every figure recalculates.

**Inventory risks**

1. No stock or inbound data — no net order quantity can be issued.
2. W33 is a Monday–Wednesday extrapolation; the full-week range is wide.
3. Stockout distortion — 37 listings carry "SELLING OUT FAST" in the title, all QL1058 white
   variants, 11,020 August units. White demand is understated by an unknown amount.
4. Legacy `134821` SKUs are excluded as instructed. They are now genuinely dead (9 units in August
   against 48,948 in June), so exclusion costs nothing — but any remaining physical stock of them
   is outside this plan.
5. Lyn is flat (108 → 112 units/day July → August) while Maggie +90%, Elsie +91% and Mary +59%.
   Worth a look — it may be a listing or traffic problem rather than demand.
6. A fulfilment backlog of 2,371 paid-unfulfilled orders was recorded on 2026-08-10. Those units are
   sold but may not yet be decremented from stock, which will distort any on-hand figure supplied.

## 5. Data quality checks

| # | Check | Result | Note |
|---|---|---|---|
| 1 | Four stores present | PASS | Active-SKU August units: Maggie 45,955, Mary 11,647, Elsie 2,226, Lyn 1,396. |
| 2 | `134821` excluded | PASS | Removed from every calculation. |
| 3 | Duplicate records | PARTIAL | No duplicate SKU/product pairs in the aggregate tabs. Order-level duplicates could not be checked — the raw order tabs are not fully readable. |
| 4 | Missing or invalid dates | PASS | All readable order lines carry a parseable date. |
| 5 | Missing SKU / store attribution | WARNING | 385 August units sit on listings with no store prefix (Mystery Gift, Ribbed Cotton LS Sculpt Top). Small, but unattributed. |
| 6 | Stockout distortion | WARNING | See risk 3. No inventory history supplied to confirm. |
| 7 | Partial current week | WARNING | W33 is Mon–Wed only. All W33 figures are estimates. |
| 8 | Partial current day | WARNING | 2026-08-13 synced at different times per store. Today vs yesterday is not a valid comparison, so no same-day SKU comparison is offered. |
| 9 | SKU code migration | WARNING | QL1047 lowercase codes stop after W30; uppercase codes begin. Same product, renumbered — do not read the lowercase decline as lost demand. |
| 10 | Dead SKUs still listed | INFO | The QP1012 range and the RIB / MT codes show zero units since June. |
| 11 | Source data completeness | **FAIL** | The Drive connector truncates every tab of the source sheet at a few hundred rows. See below. |
| 12 | Current stock / open POs | **MISSING** | Not present in the sheet. |
| 13 | Marketing scaling plan | **MISSING** | Not provided for this run. |
| 14 | Ad spend history | **MISSING** | Spend-to-units relationship cannot be estimated. |
| 15 | Supplier lead-time history | **MISSING** | 7-day lead time is an input, not an observed figure; 2-day variability is an assumption. |

### On check 11

`read_file_content` truncates each tab of the source sheet at a few hundred rows, and the sheet is
too large to export as XLSX or ODS. Direct HTTPS to `docs.google.com` is blocked by this session's
egress policy.

What that means in practice:

- The **Monthly Sales_Store** tab exported complete (970 rows) and is saved at
  `data/monthly_sku_store_sales.csv`. Store attribution, product names and the month-level trend in
  this report are read directly from it.
- The **Weekly Sales_Store** tab truncated inside the legacy `134821` block and never reached the
  active SKUs, so the weekly figures in `data/weekly_sku_sales.csv` were carried forward from the
  2026-08-13 16:05 extraction rather than re-derived.

Those carried-forward figures were validated three ways before use: daily store totals for
Aug 1–13 sum to 61,281 against 61,618 in the complete monthly export (0.55% apart); the size and
colour trend directions reproduce independently from the monthly day-rate data; and family-level
totals reconcile. The set covers 126,979 of 127,953 4-week units (99.2%).

To make future runs fully reproducible, the Weekly Sales_Store tab needs to be reachable — moving
it to the first tab position, or exporting it to its own file, would do it.
