import csv, json

rows = [json.loads(l) for l in open('records.jsonl')]
rows.sort(key=lambda r: (r['date'], r['ticket']), reverse=True)

HEADERS = [
    'Date of Request',
    'Store',
    'Order Number',
    'Customer Name',
    'Original Order - Product',
    'Original Order - Size',
    'Original Order - Color',
    'Replacement Requested - Product',
    'Replacement Requested - Size',
    'Replacement Requested - Color',
    'Reason for Replacement',
    'Conversation / Ticket ID',
]

KEYS = ['date', 'store', 'order', 'customer',
        'orig_product', 'orig_size', 'orig_color',
        'new_product', 'new_size', 'new_color',
        'reason', 'ticket']

# utf-8-sig so Excel opens it in the right encoding on a double-click
with open('replacement_requests.csv', 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
    w.writerow(HEADERS)
    for r in rows:
        w.writerow([r[k] for k in KEYS])

print('wrote', len(rows), 'rows x', len(HEADERS), 'columns')
