# Chargeback Control Room

Pulls Shopify Payments disputes from every store, consolidates them, and renders
a single self-contained HTML dashboard for monitoring chargeback performance.

## Quick start

```bash
pip install -r requirements.txt
cp .env.example .env          # then fill in each store's domain + access token

python fetch_chargebacks.py   # pull disputes  -> data/chargebacks.json
python build_dashboard.py     # render          -> dist/chargeback-dashboard.html
```

Open `dist/chargeback-dashboard.html` in a browser. It embeds its own data and
makes no network requests, so it works from disk, from a shared drive, or
published as an artifact.

### Seeing the layout before the credentials are ready

```bash
python sample_data.py
python build_dashboard.py --data data/chargebacks-sample.json
```

The dashboard renders a prominent "sample data" banner whenever the payload is
generated rather than fetched, so a demo build can never be mistaken for real
numbers.

## Credentials

Each store needs two environment variables in `.env`, keyed by a short uppercase
prefix:

```
MARY_SHOPIFY_DOMAIN=ya6ker-ps.myshopify.com
MARY_SHOPIFY_ACCESS_TOKEN=shpat_...
MARY_SHOPIFY_LABEL=Mary's Tanks        # optional display name
```

Stores are discovered automatically from every `<KEY>_SHOPIFY_DOMAIN` in the
environment — adding a store is one block in `.env`, no code change. The token
may also be spelled `SHOPIFY_TOKEN_<KEY>`.

The access token needs:

| Scope | Why |
|---|---|
| `read_shopify_payments_disputes` | the disputes themselves — required |
| `read_orders` | order number, customer name and email on each row |

Without `read_orders` the dashboard still works; run
`fetch_chargebacks.py --no-orders` and those columns read `—`.

## Commands

| Command | What it does |
|---|---|
| `python fetch_chargebacks.py` | Pull every store into `data/chargebacks.json` |
| `python fetch_chargebacks.py MARY LYN` | Pull only these stores |
| `python fetch_chargebacks.py --since 2026-01-01` | Only disputes opened on/after a date |
| `python fetch_chargebacks.py --no-orders` | Skip order lookups (much faster) |
| `python build_dashboard.py` | Render `dist/chargeback-dashboard.html` |
| `python build_dashboard.py --data <path> --out <path>` | Render a specific payload |
| `python sample_data.py` | Generate a synthetic payload for layout review |
| `python test_chargeback_model.py` | Check the status/reason taxonomy and the maths |
| `python disputes_report.py` | The older terminal report + CSV export |

A store that fails to authenticate does not abort the run — it is reported on
the console and called out in a red banner on the dashboard, so a partial
refresh can never be mistaken for a quiet month.

## What the dashboard shows

- **Where we stand** — value at risk, split between cases waiting on us and
  cases sitting with the bank; open count, cases needing action, win rate,
  worst store, top reason, and the 30-day trend direction.
- **Store scorecard** — per-store and combined totals, win/loss rates, overdue
  counts, value at risk.
- **Status & the action queue** — every status Shopify reports, plus the open
  cases needing evidence sorted by deadline, with overdue cases first.
- **Chargebacks over time** — daily / weekly / monthly, as a group total, as
  small multiples on a shared scale, or overlaid. Every chart has a table view.
- **Why customers are disputing** — reason breakdown with counts, percentages,
  per-reason win rate, and the operational fix that usually moves it.
- **Every dispute** — the full table, sortable, filterable by store, date,
  status, reason and free-text search.

Filters at the top scope every section below them, so the numbers always agree.

## How the numbers are defined

These are judgement calls, all made in one place (`chargeback_model.py`) and
covered by `test_chargeback_model.py`:

- **Open** = `needs_response`, `under_review`, and their `warning_*` inquiry
  equivalents.
- **Needs action** = `needs_response` / `warning_needs_response` only. Anything
  `under_review` is waiting on the bank, not on us.
- **Won** = `won`. **Lost** = `lost` *and* `accepted` — conceding without
  submitting evidence loses the money just the same, so it is not a neutral
  outcome.
- **Other closed** = `charge_refunded`, `warning_closed`, `response_disabled`,
  `prevented`. No verdict was reached, so these are excluded from win rate.
  `prevented` cases were blocked by Shopify before becoming chargebacks and
  need no action.
- **Win rate** = won ÷ (won + lost). Decided cases only.
- **Value at risk** = the amount of every open dispute.
- **Trend** = last 30 days vs the 30 before; ±15% is the threshold between
  increasing, decreasing and stable, and fewer than 6 cases reports
  "not enough data" rather than a spurious swing.
- **Amounts are never summed across currencies.** Each currency is totalled
  separately and shown alongside the primary one.
- An unrecognised status from Shopify falls through to `unknown` rather than
  being counted as a win — new statuses show up as their own row instead of
  quietly distorting the rate.

## Files

| File | Purpose |
|---|---|
| `shopify_client.py` | Admin API client: auth, retries, rate-limit handling, pagination |
| `chargeback_model.py` | Status/reason taxonomy, normalisation, aggregation |
| `fetch_chargebacks.py` | Multi-store pull → JSON payload |
| `build_dashboard.py` | JSON payload + template → one self-contained HTML file |
| `templates/dashboard.html` | The dashboard itself (markup, styles, charts) |
| `sample_data.py` | Synthetic payload for reviewing the layout |
| `test_chargeback_model.py` | Tests for the taxonomy and derived figures |
| `disputes_report.py` | Earlier terminal report and CSV export |

`data/` and `dist/` are gitignored: both the fetched payload and the rendered
dashboard embed customer names, emails and order numbers.

## Refreshing it regularly

The two commands are safe to run on a schedule:

```bash
cd /path/to/Shopify && python fetch_chargebacks.py && python build_dashboard.py
```

Point it at a shared location with `--out` if the team reads it from a drive.
