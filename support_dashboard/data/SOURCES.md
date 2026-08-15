# Where every number came from

All figures were pulled from Commslayer on **2026-08-15** via the Commslayer MCP
tools, plus one Shopify Admin API call.

- **Daily history: 2026-05-24 → 2026-08-15 (84 days).** This is what the dashboard's
  date picker slices; any range inside it is summed exactly.
- **Issue breakdown: 2026-07-17 → 2026-08-15**, compared with 2026-06-17 → 2026-07-16.
  Fixed windows — the issue charts do not follow the date picker.
- **Email / channel volume: three 28-day buckets** — May 24–Jun 20, Jun 21–Jul 18,
  Jul 19–Aug 15. A selected range takes a bucket when it covers at least half of it.

## Accounts (the five "stores")

| Account | ID | Shopify domain |
|---|---|---|
| Maggies Tanks | 6576 | `4r0jeh-pr.myshopify.com` |
| Mary's Tanks | 6377 | `ya6ker-ps.myshopify.com` |
| Mary and James | 6570 | `q0byfw-an.myshopify.com` |
| Lyn's Tanks | 6527 | `xywrka-k8.myshopify.com` |
| Simply Elsie | 7356 | `thyzaq-ci.myshopify.com` |

## Calls made

| Figure | Tool | Notes |
|---|---|---|
| Tickets created / closures, daily series, avg resolution time | `reports_overview` | Per account, pulled in two or three windows each to cover 2026-05-24 → 2026-08-15 without tripping the API's response-size limit. Population figures, not a sample. |
| Per-inbox tickets, inbound messages, replies sent, resolution time | `reports_inboxes` | Per store, per 28-day bucket (15 calls). This is the source of the email-volume section and of the unanswered-Facebook finding. It has no daily series, which is why email figures are bucketed rather than daily. |
| Issue categories | `reports_contact_reasons` | Per account. Commslayer derives a contact reason per conversation **from the message text**, not from agent tags. Mary's Tanks was pulled for both 30-day periods and for each of the four weeks 19 Jul – 15 Aug; the other four for the current period only. |
| Open / snoozed / resolved counts, inbox and label config | `account_overview` | Live account state at pull time. |
| Open ticket rows | `conversations_list` (status=open) | Mary's Tanks. Capped at 500 rows / 30 days by the API; pages 1, 4 and 5 of 5 were taken so the whole stale tail is present — 147 of 247 open tickets. |
| Agent performance | `reports_agents` | Current period, Mary's Tanks. |
| Shopify order counts | `GET /admin/api/2024-01/orders/count.json` | Lyn's Tanks only — the one store whose API token is present in this environment. 1,376 orders this period, 3,972 the previous one. |

## What could not be retrieved

`conversations_get` returned **"Daily message access limit reached (20,000
messages/day)"** for the whole session. Message bodies were therefore unreadable,
which is why the ticket table has no **order number** and no free-text **action
taken** column. Those two fields are inferred instead from the workflow labels the
team applies (`pfg-ready`, `refund-approved`, `ai-size-swap`, `fulfilment-error`,
and so on), which record what was agreed rather than what was written. Re-running
`build_data.py` after the quota resets, with a `conversations_get` pass over the
open tickets, would fill both columns.

Shopify tokens for the other four stores are not present in this environment, so
the customer issue rate is computed for Lyn's Tanks alone.

## Coverage

30,113 of 39,689 tickets (76%) carry a contact reason and so appear in the issue
charts. The remainder are uncategorised at source; they are still counted in every
volume, backlog and resolution figure.

## Rebuilding

```
python3 build_data.py   # figures -> data/dashboard_data.json
python3 build.py        # template.html + data -> dashboard.html
```


## Two quirks in Commslayer's own numbers

Both are handled explicitly in the dashboard rather than smoothed over.

**Closed tickets.** The period total and the day-by-day series disagree on every
store — the daily series sums 15–25% higher. It appears to count close *events*,
so a reopened-and-reclosed ticket counts twice, and it is blind to when a ticket
was opened. The dashboard therefore counts down from tickets **created** for
every resolution figure, and labels the daily series "closures recorded" rather
than "tickets closed".

| Store | Period total, Jul 17–Aug 15 | Daily series, same window |
|---|---:|---:|
| Maggies Tanks | 21,513 | 24,428 |
| Mary's Tanks | 8,756 | 10,893 |
| Mary and James | 2,265 | 2,697 |
| Lyn's Tanks | 1,028 | 1,267 |
| Simply Elsie | 862 | 1,013 |

**Average resolution time.** Same split. The closure-weighted mean of the daily
values over the 30 days to Aug 15 is about 14.7 hours; the platform's single
period figure for the same window is about 5 hours. The dashboard uses the
daily-derived figure so the headline and the chart agree with each other, and
says so on the page.

## Rebuilding after the message quota resets

`conversations_get` was capped for this whole session, so order numbers and
free-text action notes are still missing from the unresolved table. Re-running
`build_data.py` with a `conversations_get` pass over the open tickets would fill
both columns; nothing else about the build needs to change.
