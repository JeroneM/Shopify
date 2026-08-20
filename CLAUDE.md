
## Sales data source

SKU-level sales always come from the **Maggies Tank_COE** Google Sheet
(`1wx3wHF4d2DsGPlISEQ8_ArC6kY9vOkSl3wKpVoSoPPU`), refreshed daily by Coefficient.
Never substitute another sales source without saying so.

Pulling it:

- `download_file_content` with `exportMimeType: text/csv` returns the **Monthly
  Sales_Store** tab complete. This is the only tab that exports in full, and it is
  the tab to plan from.
- `read_file_content` truncates every tab after a few hundred rows. The Weekly
  Sales_Store tab never reaches past the legacy `134821` block, and the per-store
  order tabs stop after ~275 rows, so neither weekly nor daily SKU detail is
  readable that way.
- Per-SKU velocity is therefore derived by differencing the month-to-date column
  between two syncs, divided by the elapsed time between them (not by 7 — the
  syncs land mid-day). See `data/sku_last7_*.csv`.

Excluded from every calculation: SKUs beginning `134821`.

Inventory (free-to-sell, in-production) is **not** in this sheet and must be
supplied separately.
