# CommSlayer product complaint analysis

Answers: what are the biggest problems with the tank, exactly where on the garment
are customers experiencing them, and how common is each one?

## Files

| File | What it is |
|---|---|
| `records.jsonl` | One line per conversation read. Each carries the CommSlayer conversation id, contact id, date, store, and the specific problems found with the customer's own words. |
| `dataset.json` | Flattened and de-duplicated: one row per (customer, specific problem). This is what the dashboard embeds. |
| `template.html` | Dashboard source with a `/*__DATA__*/[]` data placeholder. |
| `build.py` | Injects `dataset.json` into `template.html` and writes the dashboard. |
| `complaint-dashboard.html` | Built dashboard (published as an Artifact). |

Rebuild after editing `records.jsonl`:

```
cd analysis && python3 build.py
```

## Method

Processing order is date range → CommSlayer product labels → conversations →
specific problem → dashboard. Labels used to narrow the set:
`return-exchange`, `size_issue`, `size_replacement`, `refund-request`,
`damaged-item`, `fulfilment-error`, `product-suggestions`.

Excluded: tickets only about shipping, tracking, order status, address changes,
payment or fulfilment delays; pre-purchase questions; agent messages.

Counting: each customer counted once per specific problem, and under several
problems if they reported several. Percentage is
`customers reporting the problem ÷ all customers with a product complaint in the
selected date range and store × 100`.

Where the customer did not say where or how, the problem is recorded as
`Unspecified fit/product complaint` rather than guessed.

## Scope and limits

- **Window: 1–31 August 2026.** The CommSlayer `conversations_list` API caps its
  lookback at 30 days, so earlier periods cannot be pulled through this path.
- **Sample, not census.** 64 conversations were read across the labels above.
  Ranks and shares are reliable; absolute counts are sample counts. August carried
  roughly 6,300 size-exchange and 1,900 fit-and-damage tickets in the same window.
- **One store.** The connected CommSlayer account is Maggie's Tanks (6576).
  Mary's Tanks (6377), Lyn's Tanks (6527), Simply Elsie (7356) and
  Mary & James (6570) are separate accounts, each needing its own MCP connection
  before its conversations can appear.

## No personal data

`dataset.json` and the CSV export carry only category, specific problem, customer
count, percentage and an example quote. Names, emails, order numbers, addresses,
measurements, colours, replacement and shipping details are all excluded.
`records.jsonl` keeps opaque numeric CommSlayer ids for traceability, no names or
emails.
