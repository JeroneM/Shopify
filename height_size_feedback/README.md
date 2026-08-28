# Height + size fit feedback

Customers who stated **both** their height and a size, paired with the fit outcome
and their own words about what went wrong.

## Files

| File | What it is |
| --- | --- |
| `records.jsonl` | The dataset. One JSON object per customer. Height stored as feet/inches. |
| `build.py` | Renders `records.jsonl` into `fit_by_height.html`. Run from this directory. |
| `fit_by_height.html` | Filterable table + fit-by-height-band chart. Published as an Artifact. |
| `to_csv.py` | Renders `records.jsonl` into `height_size_fit_feedback.csv`. Run from this directory. |
| `add_weight.py` | One-off migration that lifted the stated weight out of the concern text into `weight_lb`. Already applied; kept for provenance. |
| `height_size_fit_feedback.csv` | Spreadsheet export. 83 rows x 12 columns, UTF-8 with BOM. Gitignored (`*.csv`) — regenerate with `to_csv.py`. |

## Inclusion rule

A customer is included only if the conversation states, in the customer's own words:

1. a numeric height, and
2. a size — either the tank size they ordered (`Tank size ordered`) or the bra
   size they wear (`Bra size worn`).

Customers who gave a height but never named a size were **excluded**, not guessed at.
That is the single biggest reason the set is 83 and not 100+.

Height is converted at 1 in = 2.54 cm and rounded to the nearest cm in `build.py`;
the customer's original wording is kept in `h_orig`.

Weight (`weight_lb`) is recorded **only where the customer stated it** — 72 of 83.
The other 11 are null and export as `Not Specified`. Two cases were resolved by
reading rather than by picking a number:

- `C-61805` — "used to be 5'6\" 140 lbs, now 5'3\" 155 lbs" → 155 (140 is her past weight)
- `C-55386` — "138 lbs ... cites an ad showing a 170 lb model" → 138 (170 is the ad model)

The four customers whose messages were only ever read as truncated search previews
(`C-62373`, `C-62150`, `C-59181`, `C-50619`) were re-fetched in full to confirm they
genuinely stated no weight.

Note: `fit_by_height.html` does **not** show weight — the artifact predates this column.

## Scope

83 customers, messages dated 2026-06-19 to 2026-08-28, all from the Maggie's Tanks
CommSlayer account (6576) — the only account this integration is authorised for.
Mary's Tanks (6377), Lyn's Tanks (6527) and Simply Elsie (7356) are separate
accounts with their own MCP endpoints and return nothing here.

## Chart colours

The three fit outcomes are a discrete polarity scale (undersized ↔ oversized).
Both light and dark steps were checked with the dataviz skill's
`validate_palette.js` and pass every check — lightness band, chroma floor, CVD
separation, normal-vision floor and contrast.

- light: `#D98026` too small · `#12784F` good fit · `#6A4FA8` too big
- dark:  `#C67F28` too small · `#009070` good fit · `#8B7BD2` too big
