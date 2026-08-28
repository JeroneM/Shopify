import json, html

rows = [json.loads(l) for l in open('records.jsonl')]
rows.sort(key=lambda r: (r['date'], r['ticket']), reverse=True)

STORES = ["Maggie's Tanks", "Mary's Tanks", "Lyn's Tanks", "Simply Elsie"]

def unspec(v): return v.strip().lower().startswith('not specified')

for r in rows:
    fields = [r['order'], r['orig_size'], r['orig_color'], r['new_size'], r['new_color']]
    gaps = sum(1 for f in fields if unspec(f))
    r['completeness'] = 'full' if gaps == 0 else ('partial' if gaps <= 2 else 'sparse')
    r['gaps'] = gaps

data_json = json.dumps(rows, ensure_ascii=False).replace('</', '<\\/')

dates = sorted(r['date'] for r in rows)
dmin, dmax = dates[0], dates[-1]

HEAD = '''<title>Tank Exchange Requests</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Newsreader:opsz,wght@6..72,400;6..72,500;6..72,600&family=Archivo:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
:root{
  --ground:#FBFAFB; --surface:#FFFFFF; --surface-2:#F5F2F6;
  --ink:#1F1B21; --ink-2:#4A434F; --muted:#7A7280;
  --line:#E7E2E8; --line-strong:#D6CEDA;
  --accent:#7A3B5C; --accent-soft:#F3E7EE; --accent-ink:#7A3B5C;
  --gap-ink:#8A6410; --gap-bg:#FAF1DC;
  --ok-ink:#1F6152; --ok-bg:#DFF0EA;
  --shadow:0 1px 2px rgba(31,27,33,.05), 0 8px 24px -16px rgba(31,27,33,.24);
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    --ground:#17141A; --surface:#1F1B23; --surface-2:#262029;
    --ink:#F1ECF3; --ink-2:#CDC5D3; --muted:#A198AA;
    --line:#322C38; --line-strong:#443C4C;
    --accent:#DE9CBC; --accent-soft:#3A2331; --accent-ink:#EFB9D1;
    --gap-ink:#E0BB6C; --gap-bg:#3A2F17;
    --ok-ink:#8FD5C0; --ok-bg:#1B3A33;
    --shadow:0 1px 2px rgba(0,0,0,.4), 0 8px 24px -16px rgba(0,0,0,.8);
  }
}
:root[data-theme="dark"]{
  --ground:#17141A; --surface:#1F1B23; --surface-2:#262029;
  --ink:#F1ECF3; --ink-2:#CDC5D3; --muted:#A198AA;
  --line:#322C38; --line-strong:#443C4C;
  --accent:#DE9CBC; --accent-soft:#3A2331; --accent-ink:#EFB9D1;
  --gap-ink:#E0BB6C; --gap-bg:#3A2F17;
  --ok-ink:#8FD5C0; --ok-bg:#1B3A33;
  --shadow:0 1px 2px rgba(0,0,0,.4), 0 8px 24px -16px rgba(0,0,0,.8);
}

*{box-sizing:border-box}
body{
  margin:0; background:var(--ground); color:var(--ink);
  font-family:"Archivo","Helvetica Neue",Arial,sans-serif;
  font-size:15px; line-height:1.5;
  -webkit-font-smoothing:antialiased;
}
.wrap{max-width:1440px; margin:0 auto; padding:40px 28px 80px; display:flex; flex-direction:column; gap:28px}

/* ---- masthead ---- */
.masthead{display:flex; flex-direction:column; gap:10px; padding-bottom:24px; border-bottom:1px solid var(--line-strong)}
.eyebrow{
  font-family:"IBM Plex Mono",ui-monospace,monospace; font-size:11px; letter-spacing:.14em;
  text-transform:uppercase; color:var(--accent-ink);
}
h1{
  font-family:"Newsreader",Georgia,serif; font-weight:500; font-size:clamp(30px,4.2vw,46px);
  line-height:1.08; margin:0; text-wrap:balance; letter-spacing:-.01em;
}
.standfirst{margin:0; max-width:64ch; color:var(--ink-2); font-size:16px}

/* ---- summary strip ---- */
.stats{display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:1px; background:var(--line); border:1px solid var(--line); border-radius:10px; overflow:hidden}
.stat{background:var(--surface); padding:14px 16px; display:flex; flex-direction:column; gap:3px}
.stat b{font-family:"Newsreader",Georgia,serif; font-size:28px; font-weight:500; line-height:1; font-variant-numeric:tabular-nums}
.stat span{font-size:11px; letter-spacing:.08em; text-transform:uppercase; color:var(--muted); font-weight:600}

/* ---- controls ---- */
.controls{
  background:var(--surface); border:1px solid var(--line); border-radius:12px;
  padding:16px 18px; display:flex; flex-wrap:wrap; gap:16px 22px; align-items:flex-end; box-shadow:var(--shadow);
}
.field{display:flex; flex-direction:column; gap:6px; min-width:0}
.field label{font-size:11px; letter-spacing:.09em; text-transform:uppercase; color:var(--muted); font-weight:600}
input[type=date], select, input[type=search]{
  font-family:inherit; font-size:14px; color:var(--ink); background:var(--surface-2);
  border:1px solid var(--line-strong); border-radius:7px; padding:8px 10px; min-height:38px;
}
input[type=date]{font-family:"IBM Plex Mono",monospace; font-size:13px}
input[type=search]{min-width:230px}
select{min-width:170px}
input:focus-visible, select:focus-visible, button:focus-visible{
  outline:2px solid var(--accent); outline-offset:2px;
}
.dates{display:flex; gap:8px; align-items:center}
.dates .sep{color:var(--muted); font-size:13px; padding-bottom:9px}
.spacer{flex:1 1 auto}
button.reset{
  font-family:inherit; font-size:13px; font-weight:600; color:var(--ink-2); cursor:pointer;
  background:transparent; border:1px solid var(--line-strong); border-radius:7px; padding:9px 14px; min-height:38px;
}
button.reset:hover{background:var(--surface-2); color:var(--ink)}

.resultline{font-size:13px; color:var(--muted); font-variant-numeric:tabular-nums}
.resultline strong{color:var(--ink); font-weight:600}

/* ---- table ---- */
.tablewrap{border:1px solid var(--line); border-radius:12px; background:var(--surface); overflow-x:auto; box-shadow:var(--shadow)}
table{border-collapse:collapse; width:100%; min-width:1180px}
thead th{
  position:sticky; top:0; z-index:2; background:var(--surface-2);
  text-align:left; font-size:10.5px; letter-spacing:.1em; text-transform:uppercase;
  color:var(--muted); font-weight:700; padding:12px 14px; border-bottom:1px solid var(--line-strong);
  white-space:nowrap;
}
tbody td{padding:14px; border-bottom:1px solid var(--line); vertical-align:top; font-size:13.5px}
tbody tr:last-child td{border-bottom:none}
tbody tr:hover td{background:var(--surface-2)}
.mono{font-family:"IBM Plex Mono",ui-monospace,monospace; font-size:12.5px; font-variant-numeric:tabular-nums; white-space:nowrap}
.cust{font-weight:600; color:var(--ink)}
td.reason{color:var(--ink-2); min-width:270px; max-width:340px; font-size:13px}

/* paired spec cells */
.spec{display:flex; flex-direction:column; gap:5px; min-width:190px; max-width:230px}
.spec .prod{font-weight:600; color:var(--ink); line-height:1.35}
.spec dl{display:grid; grid-template-columns:auto 1fr; gap:2px 8px; margin:0}
.spec dt{font-size:10px; letter-spacing:.07em; text-transform:uppercase; color:var(--muted); font-weight:700; padding-top:2px}
.spec dd{margin:0; font-size:12.5px; color:var(--ink-2)}
.spec dd.ns{color:var(--gap-ink); font-style:italic}
td.want .prod{color:var(--accent-ink)}

.chip{
  display:inline-block; font-size:11px; font-weight:600; letter-spacing:.02em;
  padding:3px 8px; border-radius:999px; white-space:nowrap;
  background:var(--accent-soft); color:var(--accent-ink);
}
.chip.gap{background:var(--gap-bg); color:var(--gap-ink)}
.chip.ok{background:var(--ok-bg); color:var(--ok-ink)}

/* ---- coverage note ---- */
.note{
  border:1px solid var(--line-strong); border-left:3px solid var(--accent);
  background:var(--surface); border-radius:10px; padding:16px 20px;
  display:flex; flex-direction:column; gap:8px;
}
.note h2{font-family:"Newsreader",Georgia,serif; font-weight:600; font-size:17px; margin:0}
.note p{margin:0; font-size:13.5px; color:var(--ink-2); max-width:80ch}
.note ul{margin:2px 0 0; padding-left:18px; font-size:13.5px; color:var(--ink-2); display:flex; flex-direction:column; gap:4px}
.note code{font-family:"IBM Plex Mono",monospace; font-size:12.5px; background:var(--surface-2); padding:1px 5px; border-radius:4px}

.empty{padding:56px 24px; text-align:center; color:var(--muted); font-size:14px}

footer{font-size:12.5px; color:var(--muted); padding-top:8px; border-top:1px solid var(--line); display:flex; flex-wrap:wrap; gap:6px 18px}

@media (max-width:720px){
  .wrap{padding:28px 16px 64px}
  input[type=search]{min-width:0; width:100%}
  .field{flex:1 1 100%}
  .dates{width:100%}
  .dates input{flex:1 1 0}
}
@media (prefers-reduced-motion:reduce){*{animation:none!important; transition:none!important}}
</style>
'''

BODY = f'''<div class="wrap">

<header class="masthead">
  <div class="eyebrow">CommSlayer &middot; replacement &amp; exchange desk</div>
  <h1>Tank Exchange Requests</h1>
  <p class="standfirst">Every customer who asked us to swap what they received for something else &mdash; a different size, colour, fabric or style. Refund-only requests are excluded. Details are taken from what the customer actually wrote; anything they did not state is marked <em>Not Specified</em> rather than inferred.</p>
</header>

<section class="stats" id="stats" aria-label="Summary"></section>

<section class="controls" aria-label="Filters">
  <div class="field">
    <label for="f-store">Store</label>
    <select id="f-store">
      <option value="">All stores</option>
    </select>
  </div>
  <div class="field">
    <label for="f-from">Date of request</label>
    <div class="dates">
      <input type="date" id="f-from" value="{dmin}" aria-label="From date">
      <span class="sep">to</span>
      <input type="date" id="f-to" value="{dmax}" aria-label="To date">
    </div>
  </div>
  <div class="field">
    <label for="f-q">Search</label>
    <input type="search" id="f-q" placeholder="Customer, order, size, colour, reason&hellip;">
  </div>
  <div class="spacer"></div>
  <button class="reset" id="reset" type="button">Reset filters</button>
</section>

<p class="resultline" id="resultline"></p>

<div class="tablewrap">
  <table>
    <thead>
      <tr>
        <th scope="col">Date</th>
        <th scope="col">Store</th>
        <th scope="col">Order&nbsp;#</th>
        <th scope="col">Customer</th>
        <th scope="col">Original order</th>
        <th scope="col">Replacement requested</th>
        <th scope="col">Reason for replacement</th>
        <th scope="col">Ticket</th>
      </tr>
    </thead>
    <tbody id="tbody"></tbody>
  </table>
</div>
<p class="empty" id="empty" hidden>No requests match these filters.</p>

<section class="note">
  <h2>Data coverage</h2>
  <p>All {len(rows)} requests below come from the <strong>Maggie&rsquo;s Tanks</strong> CommSlayer account, which is the only account this integration is authorised for. CommSlayer keeps each store in a separate account with its own MCP endpoint, so the other three stores return no data through this connection:</p>
  <ul>
    <li><strong>Mary&rsquo;s Tanks</strong> &mdash; account <code>6377</code>, not connected</li>
    <li><strong>Lyn&rsquo;s Tanks</strong> &mdash; account <code>6527</code>, not connected</li>
    <li><strong>Simply Elsie</strong> &mdash; account <code>7356</code>, not connected</li>
  </ul>
  <p>The store filter already lists all four. Connect each account&rsquo;s MCP endpoint as a separate integration and the same pull will populate the remaining three.</p>
</section>

<footer>
  <span>Source: CommSlayer conversations, account 6576 (Maggie&rsquo;s Tanks)</span>
  <span>Requests dated {dmin} &ndash; {dmax}</span>
  <span>Refund-only tickets excluded</span>
</footer>

</div>

<script type="application/json" id="data">{data_json}</script>
<script>
(function(){{
  var ROWS = JSON.parse(document.getElementById('data').textContent);
  var STORES = {json.dumps(STORES)};
  var tbody = document.getElementById('tbody');
  var empty = document.getElementById('empty');
  var resultline = document.getElementById('resultline');
  var statsEl = document.getElementById('stats');
  var fStore = document.getElementById('f-store');
  var fFrom = document.getElementById('f-from');
  var fTo = document.getElementById('f-to');
  var fQ = document.getElementById('f-q');
  var D_MIN = {json.dumps(dmin)}, D_MAX = {json.dumps(dmax)};

  STORES.forEach(function(s){{
    var n = ROWS.filter(function(r){{ return r.store === s; }}).length;
    var o = document.createElement('option');
    o.value = s;
    o.textContent = s + ' (' + n + ')';
    if (n === 0) o.textContent = s + ' (0 \\u2014 not connected)';
    fStore.appendChild(o);
  }});

  function esc(s){{
    return String(s).replace(/[&<>"]/g, function(c){{
      return {{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}}[c];
    }});
  }}
  function isNS(v){{ return /^not specified/i.test(String(v).trim()); }}
  function ddClass(v){{ return isNS(v) ? ' class="ns"' : ''; }}

  function specCell(prod, size, color){{
    return '<div class="spec">' +
      '<div class="prod">' + esc(prod) + '</div>' +
      '<dl>' +
        '<dt>Size</dt><dd' + ddClass(size) + '>' + esc(size) + '</dd>' +
        '<dt>Colour</dt><dd' + ddClass(color) + '>' + esc(color) + '</dd>' +
      '</dl></div>';
  }}

  function render(){{
    var store = fStore.value;
    var from = fFrom.value || D_MIN;
    var to = fTo.value || D_MAX;
    var q = fQ.value.trim().toLowerCase();

    var out = ROWS.filter(function(r){{
      if (store && r.store !== store) return false;
      if (r.date < from || r.date > to) return false;
      if (q) {{
        var hay = [r.customer, r.order, r.orig_product, r.orig_size, r.orig_color,
                   r.new_product, r.new_size, r.new_color, r.reason, r.ticket, r.store]
                   .join(' ').toLowerCase();
        if (hay.indexOf(q) === -1) return false;
      }}
      return true;
    }});

    tbody.innerHTML = out.map(function(r){{
      return '<tr>' +
        '<td class="mono">' + esc(r.date) + '</td>' +
        '<td><span class="chip">' + esc(r.store) + '</span></td>' +
        '<td class="mono">' + esc(r.order) + '</td>' +
        '<td class="cust">' + esc(r.customer) + '</td>' +
        '<td>' + specCell(r.orig_product, r.orig_size, r.orig_color) + '</td>' +
        '<td class="want">' + specCell(r.new_product, r.new_size, r.new_color) + '</td>' +
        '<td class="reason">' + esc(r.reason) + '</td>' +
        '<td class="mono">' + esc(r.ticket) + '</td>' +
      '</tr>';
    }}).join('');

    empty.hidden = out.length > 0;
    resultline.innerHTML = 'Showing <strong>' + out.length + '</strong> of ' + ROWS.length +
      ' replacement requests' + (store ? ' &middot; ' + esc(store) : '') + '.';

    var full = out.filter(function(r){{ return r.completeness === 'full'; }}).length;
    var withOrder = out.filter(function(r){{ return !isNS(r.order); }}).length;
    var sized = out.filter(function(r){{ return !isNS(r.new_size); }}).length;
    var cards = [
      [out.length, 'Requests'],
      [withOrder, 'With order number'],
      [sized, 'Replacement size stated'],
      [full, 'Fully specified'],
      [out.length - full, 'Has gaps']
    ];
    statsEl.innerHTML = cards.map(function(c){{
      return '<div class="stat"><b>' + c[0] + '</b><span>' + c[1] + '</span></div>';
    }}).join('');
  }}

  [fStore, fFrom, fTo].forEach(function(el){{ el.addEventListener('change', render); }});
  fQ.addEventListener('input', render);
  document.getElementById('reset').addEventListener('click', function(){{
    fStore.value = ''; fFrom.value = D_MIN; fTo.value = D_MAX; fQ.value = ''; render();
  }});

  render();
}})();
</script>
'''

open('exchanges.html','w').write(HEAD + BODY)
print('rows:', len(rows))
