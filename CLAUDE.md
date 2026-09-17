
## Sales data source

SKU-level sales always come from the **Maggies Tank_COE** Google Sheet
(`1wx3wHF4d2DsGPlISEQ8_ArC6kY9vOkSl3wKpVoSoPPU`), refreshed daily by Coefficient.
Never substitute another sales source without saying so.

Pulling it:

- **As of 2026-09-09 the sheet is no longer readable.** `download_file_content`
  (csv and tsv) returns "File too large for export" — the workbook passed the
  export size limit around 5.1 MB in late August and is now ~5.8 MB. The
  `Monthly Sales_Store` and `Weekly Sales_Store` tabs have also been removed;
  only the four raw per-store order tabs remain.
- `read_file_content` still returns something, but truncates every tab after
  ~275 rows. The order tabs are sorted oldest-first, so the readable rows reach
  only mid-July. No current SKU detail can be extracted.
- Until this is fixed, SKU velocity comes from the last usable pull
  (`data/sku_store_windows_2026-08-25.csv`, the 13–25 Aug window) plus whatever
  actuals the user supplies in an attached workbook. Say so explicitly in any
  report built this way.
- Two fixes would restore it: sort each store's order tab newest-first, or add a
  SKU-level pivot in a separate, smaller file.
- Per-SKU velocity is therefore derived by differencing the month-to-date column
  between two syncs, divided by the elapsed time between them (not by 7 — the
  syncs land mid-day). See `data/sku_last7_*.csv`.

Excluded from every calculation: SKUs beginning `134821`.

Inventory (free-to-sell, in-production) is **not** in this sheet and must be
supplied separately.

## SKU renames — apply before joining sales to inventory

The sales sheet and the inventory exports drift apart: ranges get renumbered in
one and not the other. Always canonicalise before matching, or demand lands on a
SKU with no stock while stock sits on a SKU with no demand. Each of these has
already produced a wrong order at least once.

| Old code (sales) | Current code (inventory) | Notes |
|---|---|---|
| `QL1058-*` | `QL1076-*` | Renamed 2026-09-17. Built-in Bra Comfort Tank — the largest range. Straight prefix swap; colour and size suffixes are unchanged. |
| `QA1071-*` | `QL1074-*` | Renamed ~2026-09-02. Brief / Leakproof Underwear. Straight prefix swap. |
| `QL1047-BLK/GRY/ARMY/KHK/RED-{S,M,L,XL,2XL}` | `QL1047-{black,gray,green,khaki,red}-{s,m,l,x,xxl}` | Two code schemes for the same garment, both live in the sales sheet. `ARMY`=Army green→`green`, `XL`→`x`, `2XL`→`xxl`. Confirmed from the sheet's own product names. |

Still unresolved — do not guess, ask:

- `QL1074` colours. Sales record **CaramelOrange, LavaRed, Nude, Wheat**;
  inventory records **Brown, Lava, Pink, Purple**. LavaRed↔Lava is near-certain,
  the rest are not. ~1,668 units of inventory sit under codes with no sales.
- Within `QL1074`, the SKU colour code and the product-name colour disagree
  (`QA1071-Beige-*` is titled "Nude"; `QA1071-khaki-*` is titled "Wheat"), which
  is probably how the drift started.
