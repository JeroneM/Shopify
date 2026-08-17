# Customer Issue Dashboard

Builds a complete-population customer-issue dashboard for four Commslayer accounts
covering **1 July – 17 August 2026**.

Published artifact: <https://claude.ai/code/artifact/ec8f9d75-a5b9-4537-a6f8-944ed0f0d1fd>

## Why aggregates instead of ticket rows

`conversations_list` caps at **500 records per account** (10 pages × 50) and accepts
`days` of at most **30**, so it can neither reach 1 July nor enumerate the 48k+ tickets
in the window. Every figure therefore comes from the **reporting endpoints**, which
aggregate the whole population server-side:

| Endpoint | Supplies |
|---|---|
| `reports_contact_reasons` | complete issue / issue-reason counts for any date range |
| `reports_overview` | complete created & closed totals plus daily series |

## Accounts

| Account | ID | Timezone | Tickets | Classified |
|---|---|---|---|---|
| Simply Elsie | 7356 | UTC | 1,110 | 887 |
| Maggie's Tanks | 6576 | UTC | 31,533 | 24,096 |
| Mary's Tanks | 6377 | UTC+10 | 13,253 | 11,372 |
| Lyn's Tanks | 6527 | UTC | 2,643 | 2,319 |

Account 6570 (*Mary and James*) is deliberately excluded.

## Layout of this directory

| File | Role |
|---|---|
| `nodes.py` | Mary's contact-reason id → (name, parent) registry and the week grid |
| `elsie.py` `maggies.py` `mary.py` `lyns.py` | per-account weekly `own_amount` counts, plus an independently fetched full-period total used as a checksum, plus daily created/closed series |
| `mapping.py` | maps Commslayer contact-reason paths onto the 10 reported issues and their reasons |
| `build.py` | validates, expands the mapping and emits `dashboard_data.json` |
| `dashboard.html` | the dashboard, with `dashboard_data.json` inlined |

Rebuild with:

```sh
cd issue_dashboard && python3 build.py
```

`build.py` prints unmapped paths (currently zero) and any daily-vs-period variance.

## Resolution

Each account is fetched over **seven non-overlapping weekly windows** that tile the
period exactly. Weekly is the finest affordable granularity — the contact-reason tree
returns the full taxonomy on every call regardless of window size, so per-day fetches
would be 192 calls of identical size.

Consequently:

- **Ticket volume** is exact per day (from the `reports_overview` daily series).
- **Issue and reason splits** are exact per week.
- The dashboard's date filter **snaps outward to whole weeks** and always shows the
  effective range. Nothing is interpolated between weeks.

## Tickets vs issues

One ticket can carry more than one issue. 22 source reasons are inherently multi-topic
and expand to several `(issue, reason)` pairs — e.g. *"item arrived damaged and has a
sizing issue"* becomes 1 ticket and 2 issues. Across the period: **48,476 tickets →
51,802 issues** (1.067 per ticket).

## Verification

`build.py` reconciles the seven weekly windows against a separately fetched
full-period total for every account. Result: **3 of 279 reason nodes differ, by 4
tickets in 38,674 (0.01%)**, caused by tickets being reclassified between calls.

Two variances are surfaced in the dashboard rather than smoothed away:

1. **Mary's UTC+10 boundary** — its daily series covers 13,190 of 13,253 tickets
   (0.5%); the remainder falls outside the UTC day buckets. The dashboard headlines
   48,476 (sum of daily series) rather than 48,539 (sum of period totals) so that no
   two sections can disagree.
2. **Two closure definitions** — the daily `closed` series (51,165) counts closure
   events including tickets raised before the window, while `closed_tickets.current`
   (43,198) is a created-cohort measure. Only the daily series filters by date, so it
   is used throughout; this is why the resolution rate can exceed 100% when the
   backlog shrinks.

## Known limits of the source

- **Fit direction is not recorded.** "Too small" vs "too big" cannot be derived from
  the aggregates; sizing reasons name what the source actually states. Reading it would
  require per-message retrieval, which the 500-record cap makes impossible at this scale.
- **No colour reason exists** in any of the four taxonomies, so colour surfaces only
  where a reason explicitly names it.
- Anything the helpdesk left unclassified is reported as **Other / Needs review**.
