# Customer Issue Dashboard

Builds a complete-population customer-issue dashboard for four Commslayer accounts
covering **1 July – 28 September 2026** for all four accounts.

Published artifact: <https://claude.ai/code/artifact/ec8f9d75-a5b9-4537-a6f8-944ed0f0d1fd>

## Why aggregates instead of ticket rows

`conversations_list` caps at **500 records per account** (10 pages × 50) and accepts
`days` of at most **30**, so it can neither reach 1 July nor enumerate the 144k+ tickets
in the window. Every figure therefore comes from the **reporting endpoints**, which
aggregate the whole population server-side:

| Endpoint | Supplies |
|---|---|
| `reports_contact_reasons` | complete issue / issue-reason counts for any date range |
| `reports_overview` | complete created & closed totals plus daily series |

## Accounts

| Account | ID | Timezone | Tickets | Classified |
|---|---|---|---|---|
| Simply Elsie | 7356 | UTC | 3,148 | 2,731 |
| Maggie's Tanks | 6576 | UTC | 114,209 | 94,337 |
| Mary's Tanks | 6377 | UTC+10 | 24,261 | 20,948 |
| Lyn's Tanks | 6527 | UTC | 3,067 | 2,723 |
| **Total** | | | **144,685** | **120,739** |

Each account has its own Commslayer connection (`mcp__CommSlayer_Simply_Elsie__*`,
`mcp__Commslayer__*` = Maggie's, `mcp__Commslayer_Mary_s_Tank__*`, `mcp__Commslayer_Lyn_s__*`),
so all four can be refreshed independently.

Account 6570 (*Mary and James*) is deliberately excluded.

## Layout of this directory

| File | Role |
|---|---|
| `nodes.py` | the week grid (and a legacy Mary's id → (name, parent) registry, no longer used) |
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

Each account is fetched over **thirteen non-overlapping weekly windows** that tile the
period exactly. Weekly is the finest affordable granularity — the contact-reason tree
returns the full taxonomy on every call regardless of window size, so per-day fetches
would be 360 calls of identical size.

Consequently:

- **Ticket volume** is exact per day (from the `reports_overview` daily series).
- **Issue and reason splits** are exact per week.
- The dashboard's date filter **snaps outward to whole weeks** and always shows the
  effective range. Nothing is interpolated between weeks.

## Coverage

All four stores are covered to the **same date**, 28 Sep 2026 — the last fully-elapsed day.
Every account now has its own connection, so each is fetched over the same thirteen weekly
windows.

Each store still carries `covTo` / `covWk` in `dashboard_data.json`, and days or weeks past a
store's coverage would be `null` — never `0`. That machinery is currently a no-op but is kept:
if a store ever falls behind, the dashboard shows **Incomplete Data**, names the short stores,
prints `—` in their columns, and excludes them from the KPIs, totals and chart for that range
rather than counting them as zero.

## History is not frozen

Commslayer keeps classifying tickets **after** the fact, so a window captured weeks ago
understates itself. Measured on this refresh: Simply Elsie's 1 Jul – 25 Aug was 1,292 classified
tickets when captured on 8 Sep and is **1,337** now (+3.5%), almost all of it in the last week of
the window (19–25 Aug went 323 → 370).

**Every week for every store is therefore re-fetched on each refresh**, not carried forward.
Extending the grid without re-fetching history would silently understate the older weeks.

## Tickets vs issues

One ticket can carry more than one issue. 29 source reasons are inherently multi-topic
and expand to several `(issue, reason)` pairs — e.g. *"item arrived damaged and has a
sizing issue"* becomes 1 ticket and 2 issues. Across the dataset: **144,685 tickets,
120,739 of them classified → 163,566 issues** (1.13 issues per classified ticket).

Classification coverage is **83.4%**; the remainder carry no contact reason at source. The issue
table, breakdown and issue KPIs count the classified population, while Total Tickets counts every
ticket — so issue counts do not add up to the ticket total, by design.

## Verification

`build.py` reconciles the thirteen weekly windows against a separately fetched full-period
total for every account. Result on this refresh: **398 reason nodes, 0 differences** — all four
accounts reconcile exactly, and each store's daily series sums to its own reported period total
to the ticket (`dayDelta = 0` for all four).

One variance remains and is surfaced in the dashboard rather than smoothed away:

- **Two closure definitions** — the daily `closed` series (170,336) counts closure events
  including tickets raised before the window, while `closed_tickets.current` (130,321) is a
  created-cohort measure. Only the daily series filters by date, so it is used throughout; this
  is why the resolution rate can exceed 100% when the backlog shrinks.

Mary's UTC+10 boundary gap (63 tickets in earlier builds) is **gone**: the API now returns its
dates on the `+10:00` offset and its daily series reconciles exactly.

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

- **8 Sep 2026** - week 10 (2-7 Sep) added and week 9 re-fetched. The dataset now ends on 7 Sep, the
  last fully-elapsed day, so it contains **no partial days at all** - previous builds ended on the day
  they ran and their final bucket was short (1 Sep was 338 when captured mid-morning, actually 1,824;
  25 Aug was 249, actually 1,467). Both corrected. Still Maggie's only. 18 further contact-reason nodes
  mapped, including three new multi-issue ones (item damage and size exchange, item fit and refund
  request, order and discount inquiry).

- **29 Sep 2026** - **all four stores brought current to 28 Sep** and the entire dataset re-fetched.
  Simply Elsie, Mary's Tanks and Lyn's Tanks each gained their own Commslayer connection, ending the
  single-account pinning that had frozen them at 25 Aug; the grid went from ten weeks to thirteen
  (1 Jul - 28 Sep, 90 days, no partial days). Crucially, **all 13 weeks were re-fetched for every
  store rather than extended**, after discovering that Commslayer keeps classifying tickets after
  capture - Elsie's Jul-Aug window had grown 3.5% since 8 Sep. All four accounts now reconcile
  exactly (398 nodes, 0 differences) and every daily series matches its period total to the ticket.
  13 new contact-reason nodes mapped. Dataset: 144,685 tickets, 120,739 classified, 163,566 issues.

  Note on interpretation: Maggie's **re-cut its fit taxonomy** in the week of 2 Sep -
  *"item fit and damage issue"* collapsed (624 -> 36/wk) and was replaced by *"item fit issue"*
  (63 -> 1,533/wk) and *"item fit and refund request"* (0 -> 1,143/wk). Sizing, Refund and Product
  Quality moves across that boundary are therefore substantially reclassification, not a change in
  what customers wrote in about.
