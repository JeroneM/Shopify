# Customer Issue Dashboard

Builds a complete-population customer-issue dashboard for four Commslayer accounts
covering **1 July – 25 August 2026** for all four accounts, and on to **1 September** for
Maggie's Tanks (see *Coverage* below)..

Published artifact: <https://claude.ai/code/artifact/ec8f9d75-a5b9-4537-a6f8-944ed0f0d1fd>

## Why aggregates instead of ticket rows

`conversations_list` caps at **500 records per account** (10 pages × 50) and accepts
`days` of at most **30**, so it can neither reach 1 July nor enumerate the 74k+ tickets
in the window. Every figure therefore comes from the **reporting endpoints**, which
aggregate the whole population server-side:

| Endpoint | Supplies |
|---|---|
| `reports_contact_reasons` | complete issue / issue-reason counts for any date range |
| `reports_overview` | complete created & closed totals plus daily series |

## Accounts

| Account | ID | Timezone | Tickets | Classified |
|---|---|---|---|---|
| Simply Elsie | 7356 | UTC | 1,561 | 1,292 |
| Maggie's Tanks | 6576 | UTC | 53,749 | 42,677 |
| Mary's Tanks | 6377 | UTC+10 | 16,304 | 14,032 |
| Lyn's Tanks | 6527 | UTC | 2,815 | 2,484 |

Account 6570 (*Mary and James*) is deliberately excluded.

## Layout of this directory

| File | Role |
|---|---|
| `nodes.py` | Mary's contact-reason id → (name, parent) registry and the week grid |
| `elsie.py` `maggies.py` `mary.py` `lyns.py` | per-account weekly `own_amount` counts, an independently fetched full-period checksum, a `WINDOW` dict for a named ad-hoc range, and daily created/closed series |
| `mapping.py` | maps Commslayer contact-reason paths onto the 10 reported issues and their reasons |
| `build.py` | validates, expands the mapping and emits `dashboard_data.json` |
| `dashboard.html` | the dashboard, with `dashboard_data.json` inlined |

Rebuild with:

```sh
cd issue_dashboard && python3 build.py
```

`build.py` prints unmapped paths (currently zero) and any daily-vs-period variance.

## Resolution

Each account is fetched over **nine non-overlapping weekly windows** that tile the
period exactly. Weekly is the finest affordable granularity — the contact-reason tree
returns the full taxonomy on every call regardless of window size, so per-day fetches
would be 252 calls of identical size.

Consequently:

- **Ticket volume** is exact per day (from the `reports_overview` daily series).
- **Issue and reason splits** are exact per week.
- The dashboard's date filter **snaps outward to whole weeks** and always shows the
  effective range. Nothing is interpolated between weeks.

## Coverage

Stores are **not covered to the same date**. Commslayer's connection is now pinned to one
account at a time and no longer exposes account switching, so from 1 Sep 2026 only the
currently-connected account can be refreshed:

| Store | Covered to |
|---|---|
| Simply Elsie, Mary's Tanks, Lyn's Tanks | 25 Aug 2026 |
| Maggie's Tanks | 1 Sep 2026 |

Each store carries `covTo` / `covWk` in `dashboard_data.json`, and days or weeks past a store's
coverage are `null` — never `0`. Any range ending after 25 August makes the dashboard show
**Incomplete Data**, name the short stores, and print `—` in their columns; those stores are
excluded from the KPIs, totals and chart for that range rather than counted as zero. To restore
four-store coverage, connect the other accounts' `mcp_url` values as separate integrations.

## Tickets vs issues

One ticket can carry more than one issue. 26 source reasons are inherently multi-topic
and expand to several `(issue, reason)` pairs — e.g. *"item arrived damaged and has a
sizing issue"* becomes 1 ticket and 2 issues. Across the dataset: **74,366 tickets →
82,536 issues** (1.110 per ticket).

## Verification

`build.py` reconciles the nine weekly windows against a separately fetched
full-period total for every account. Result: **1 of 365 reason nodes differs, by 1
ticket in 60,485 (0.002%)**, caused by a ticket being reclassified between calls.

Two variances are surfaced in the dashboard rather than smoothed away:

1. **Mary's UTC+10 boundary** — its daily series covers 16,241 of 16,304 tickets
   (0.4%); the remainder falls outside the UTC day buckets. The dashboard headlines
   74,366 (sum of daily series) rather than 74,429 (sum of period totals) so that no
   two sections can disagree.
2. **Two closure definitions** — the daily `closed` series (76,522) counts closure
   events including tickets raised before the window, while `closed_tickets.current`
   (72,306) is a created-cohort measure. Only the daily series filters by date, so it
   is used throughout; this is why the resolution rate can exceed 100% when the
   backlog shrinks.

## Known limits of the source

- **Fit direction is not recorded.** "Too small" vs "too big" cannot be derived from
  the aggregates; sizing reasons name what the source actually states. Reading it would
  require per-message retrieval, which the 500-record cap makes impossible at this scale.
- **Colour is barely recorded.** It surfaces only where a reason explicitly names it.
  Maggie's added *"order exchange and colour correction"* in August, which is the bulk of the
  colour row; the true rate of colour complaints is still not observable.
- Anything the helpdesk left unclassified is reported as **Other / Needs review**.

## Refresh log

- **25 Aug 2026** - extended from 17 Aug to 25 Aug. Week 7 was re-fetched as 12-18 Aug (it had
  been a truncated 12-17 Aug) and week 8 (19-25 Aug) added, so the grid is eight clean 7-day
  tiles. 17 Aug itself grew from 320 to 452 tickets on Mary's alone, because the original
  harvest caught that day mid-morning. Around 40 new contact-reason nodes appeared across the
  accounts and were mapped, two of which change what the dashboard can see: Maggie's
  *"order exchange and colour correction"* (first genuine colour signal) and *"item fit issue"*
  (first pure sizing reason with no other topic attached). 25 Aug is a partial day.

- **1 Sep 2026** - week 9 (26 Aug - 1 Sep) added and week 8 re-fetched now that 25 Aug is complete
  (25 Aug went from 249 to 1,467 tickets on Maggie's, having been ~5h of data before). Only Maggie's
  could be refreshed: the Commslayer connection lost account switching, so per-store coverage was
  introduced rather than letting a one-store week be summed into a four-store period. ~16 further
  contact-reason nodes mapped. 1 Sep is a partial day.
