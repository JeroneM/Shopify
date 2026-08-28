# Customer replacement / exchange requests

Replacement and exchange requests pulled from CommSlayer conversations, with the
original order and the requested swap read out of the customer's own messages.

## Files

| File | What it is |
| --- | --- |
| `records.jsonl` | The dataset. One JSON object per request. |
| `build.py` | Renders `records.jsonl` into `exchanges.html`. Run it from this directory. |
| `exchanges.html` | Filterable table (date range, store, keyword search). Published as an Artifact. |
| `to_csv.py` | Renders `records.jsonl` into `replacement_requests.csv`. Run it from this directory. |
| `replacement_requests.csv` | Spreadsheet export. 102 rows x 12 columns, UTF-8 with BOM so Excel opens it correctly. |

## Scope

102 requests, dated 2026-07-13 to 2026-08-28.

Only **replacement / exchange** requests are included. Refund-only and
plain-return requests are excluded, even where CommSlayer's `return-exchange`
auto-label fired on them — that label has a high false-positive rate for
refunds, so each conversation was read before inclusion.

Records were sourced from the `pfg-ready` and `size_replacement` labels (the
Perfect Fit Guarantee replacement pipeline), which track confirmed exchanges far
more precisely than `return-exchange` alone.

Nothing is inferred. Where a customer never stated the original size, colour or
order number, the field reads `Not Specified`.

## Store coverage

All 102 records are from **Maggie's Tanks** (CommSlayer account `6576`), the only
account the current MCP integration is authorised for. CommSlayer keeps each
store in a separate account with its own endpoint, so these return no data here:

- Mary's Tanks — account `6377`
- Lyn's Tanks — account `6527`
- Simply Elsie — account `7356`

The store filter in `exchanges.html` already lists all four. Connect each
account's MCP endpoint as a separate integration and re-run the pull to populate
the remaining three.

## Record shape

```json
{
  "date": "2026-08-25",
  "store": "Maggie's Tanks",
  "order": "#50766",
  "customer": "Dorothy Gerdes",
  "orig_product": "Tank top (3 items)",
  "orig_size": "Small",
  "orig_color": "1 Black, 2 Nude",
  "new_product": "Tank top (3 items)",
  "new_size": "Medium",
  "new_color": "1 Black, 2 Nude",
  "reason": "Too small and snug despite measuring before ordering",
  "ticket": "C-59895"
}
```

`build.py` derives a `completeness` field at render time from how many of
`order`, `orig_size`, `orig_color`, `new_size`, `new_color` are `Not Specified`.
