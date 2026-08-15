# Where every number came from

All figures were pulled from Commslayer on **2026-08-15** (about 11:00 UTC) via the
Commslayer MCP tools, plus one Shopify Admin API call. Reporting window
**2026-07-17 → 2026-08-15**, compared with **2026-06-17 → 2026-07-16**.

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
| Tickets created / closed, daily series, avg resolution time | `reports_overview` | Per account, current period. Population figures, not a sample. |
| Per-inbox created / closed / replies / resolution time | `reports_inboxes` | Both periods. This is what separates email from Facebook and exposes the unanswered-Facebook problem. |
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
