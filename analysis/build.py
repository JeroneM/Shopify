import json, io, os
rows = json.load(open('/home/user/Shopify/analysis/dataset.json'))
data = [{"c":r["contact"],"d":r["date"],"s":r["store"],"cat":r["cat"],"p":r["prob"],"q":r["quote"]} for r in rows]
tpl = open('/home/user/Shopify/analysis/template.html').read()
out = tpl.replace('/*__DATA__*/[]', json.dumps(data, ensure_ascii=False, separators=(',',':')))
dest = '/home/user/Shopify/analysis/complaint-dashboard.html'
open(dest,'w').write(out)
print(dest, os.path.getsize(dest), 'bytes,', len(data), 'rows')
