import csv, json

rows = [json.loads(l) for l in open('records.jsonl')]

# Convert height once, here, exactly as build.py does: 1 in = 2.54 cm, nearest cm.
for r in rows:
    r['cm'] = round((r['ft'] * 12 + r['in']) * 2.54)

# Same order as the artifact: shortest to tallest.
rows.sort(key=lambda r: (r['cm'], r['customer']))

HEADERS = [
    'Date',
    'Store',
    'Order Number',
    'Customer Name',
    'Customer Height (cm)',
    'Customer Height (as stated)',
    'Size Ordered/Worn',
    'Size Basis',
    'Fit Feedback',
    "Customer's Exact Fit Concern",
    'Conversation / Ticket ID',
]

KEYS = ['date', 'store', 'order', 'customer', 'cm', 'h_orig',
        'size', 'basis', 'fit', 'concern', 'ticket']

# utf-8-sig so Excel picks up the encoding on a double-click
with open('height_size_fit_feedback.csv', 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
    w.writerow(HEADERS)
    for r in rows:
        w.writerow([r[k] for k in KEYS])

print('wrote', len(rows), 'rows x', len(HEADERS), 'columns')
