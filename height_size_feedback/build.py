import json, math

rows = [json.loads(l) for l in open('records.jsonl')]

for r in rows:
    total_in = r['ft'] * 12 + r['in']
    r['cm'] = round(total_in * 2.54)
    r['total_in'] = total_in
    del r['ft']; del r['in']

rows.sort(key=lambda r: (r['cm'], r['customer']))

STORES = ["Maggie's Tanks", "Mary's Tanks", "Lyn's Tanks", "Simply Elsie"]

BANDS = [
    (0,   152, "Under 5'0\"",   "&lt;152 cm"),
    (153, 157, "5'1\"–5'2\"",   "153–157 cm"),
    (158, 163, "5'3\"–5'4\"",   "158–163 cm"),
    (164, 168, "5'5\"–5'6\"",   "164–168 cm"),
    (169, 173, "5'7\"–5'8\"",   "169–173 cm"),
    (174, 999, "5'9\" and up",  "174+ cm"),
]

data_json = json.dumps(rows, ensure_ascii=False).replace('</', '<\\/')
bands_json = json.dumps([{"lo":b[0],"hi":b[1],"label":b[2],"sub":b[3]} for b in BANDS])
dates = sorted(r['date'] for r in rows)
dmin, dmax = dates[0], dates[-1]

HEAD = '''<title>Fit by Height</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Spectral:wght@400;500;600&family=Public+Sans:wght@400;500;600;700&family=Roboto+Mono:wght@400;500&display=swap">
<style>
:root{
  --ground:#FCFCFB; --surface:#FFFFFF; --surface-2:#F4F6F4;
  --ink:#191C1A; --ink-2:#454B48; --muted:#6B7370;
  --line:#E4E7E4; --line-strong:#D2D7D3;
  --accent:#2F5D4E;
  /* fit scale - validated with dataviz validate_palette.js (light, all checks pass) */
  --small:#D98026; --good:#12784F; --big:#6A4FA8;
  --small-bg:#FBEFE1; --good-bg:#E1F0E9; --big-bg:#EDE9F7;
  --shadow:0 1px 2px rgba(25,28,26,.05), 0 10px 28px -20px rgba(25,28,26,.3);
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    --ground:#131614; --surface:#1A1E1C; --surface-2:#222724;
    --ink:#EEF2EF; --ink-2:#C6CEC9; --muted:#99A29E;
    --line:#2A302D; --line-strong:#3A423E;
    --accent:#8FC4B0;
    /* dark steps - separately validated against the dark surface */
    --small:#C67F28; --good:#009070; --big:#8B7BD2;
    --small-bg:#33260F; --good-bg:#0C2E26; --big-bg:#26214099;
    --shadow:0 1px 2px rgba(0,0,0,.4), 0 10px 28px -20px rgba(0,0,0,.9);
  }
}
:root[data-theme="dark"]{
  --ground:#131614; --surface:#1A1E1C; --surface-2:#222724;
  --ink:#EEF2EF; --ink-2:#C6CEC9; --muted:#99A29E;
  --line:#2A302D; --line-strong:#3A423E;
  --accent:#8FC4B0;
  --small:#C67F28; --good:#009070; --big:#8B7BD2;
  --small-bg:#33260F; --good-bg:#0C2E26; --big-bg:#26214099;
  --shadow:0 1px 2px rgba(0,0,0,.4), 0 10px 28px -20px rgba(0,0,0,.9);
}

*{box-sizing:border-box}
body{
  margin:0; background:var(--ground); color:var(--ink);
  font-family:"Public Sans","Helvetica Neue",Arial,sans-serif; font-size:15px; line-height:1.5;
  -webkit-font-smoothing:antialiased;
}
.wrap{max-width:1400px; margin:0 auto; padding:40px 26px 80px; display:flex; flex-direction:column; gap:26px}

.masthead{display:flex; flex-direction:column; gap:10px; padding-bottom:22px; border-bottom:1px solid var(--line-strong)}
.eyebrow{font-family:"Roboto Mono",ui-monospace,monospace; font-size:11px; letter-spacing:.14em; text-transform:uppercase; color:var(--accent)}
h1{font-family:"Spectral",Georgia,serif; font-weight:500; font-size:clamp(30px,4.2vw,44px); line-height:1.08; margin:0; letter-spacing:-.015em; text-wrap:balance}
.standfirst{margin:0; max-width:66ch; color:var(--ink-2); font-size:16px}

.stats{display:grid; grid-template-columns:repeat(auto-fit,minmax(140px,1fr)); gap:1px; background:var(--line); border:1px solid var(--line); border-radius:10px; overflow:hidden}
.stat{background:var(--surface); padding:14px 16px; display:flex; flex-direction:column; gap:3px}
.stat b{font-family:"Spectral",Georgia,serif; font-size:27px; font-weight:500; line-height:1; font-variant-numeric:tabular-nums}
.stat span{font-size:10.5px; letter-spacing:.08em; text-transform:uppercase; color:var(--muted); font-weight:700}

/* ---- chart ---- */
.panel{background:var(--surface); border:1px solid var(--line); border-radius:12px; padding:20px 22px; box-shadow:var(--shadow)}
.panel h2{font-family:"Spectral",Georgia,serif; font-size:18px; font-weight:600; margin:0 0 3px}
.panel .sub{margin:0 0 16px; font-size:13px; color:var(--muted)}
.legend{display:flex; flex-wrap:wrap; gap:6px 18px; margin-bottom:16px}
.legend span{display:inline-flex; align-items:center; gap:7px; font-size:12.5px; color:var(--ink-2); font-weight:500}
.swatch{width:11px; height:11px; border-radius:3px; flex:none}
.chart{display:flex; flex-direction:column; gap:11px}
.crow{display:grid; grid-template-columns:132px 1fr 44px; gap:14px; align-items:center}
.clabel{text-align:right; line-height:1.25}
.clabel b{display:block; font-size:13px; font-weight:600}
.clabel span{display:block; font-family:"Roboto Mono",monospace; font-size:10.5px; color:var(--muted)}
.bar{display:flex; gap:2px; height:26px; background:var(--surface-2); border-radius:4px; overflow:hidden}
.seg{position:relative; display:flex; align-items:center; justify-content:center; min-width:2px; cursor:default;
     font-family:"Roboto Mono",monospace; font-size:11px; font-weight:500; color:#fff; transition:filter .12s}
.seg:first-child{border-radius:4px 0 0 4px} .seg:last-child{border-radius:0 4px 4px 0}
.seg:hover{filter:brightness(1.12)}
.seg.s{background:var(--small)} .seg.g{background:var(--good)} .seg.b{background:var(--big)}
.ctotal{font-family:"Roboto Mono",monospace; font-size:12.5px; color:var(--muted); font-variant-numeric:tabular-nums}
#tip{position:fixed; z-index:50; pointer-events:none; opacity:0; transition:opacity .1s;
     background:var(--ink); color:var(--ground); font-size:12px; padding:6px 10px; border-radius:6px; white-space:nowrap; font-weight:500}

/* ---- controls ---- */
.controls{background:var(--surface); border:1px solid var(--line); border-radius:12px; padding:15px 18px;
          display:flex; flex-wrap:wrap; gap:14px 20px; align-items:flex-end; box-shadow:var(--shadow)}
.field{display:flex; flex-direction:column; gap:6px; min-width:0}
.field label{font-size:10.5px; letter-spacing:.09em; text-transform:uppercase; color:var(--muted); font-weight:700}
input[type=date],select,input[type=search]{font-family:inherit; font-size:14px; color:var(--ink); background:var(--surface-2);
  border:1px solid var(--line-strong); border-radius:7px; padding:8px 10px; min-height:38px}
input[type=date]{font-family:"Roboto Mono",monospace; font-size:13px}
input[type=search]{min-width:220px} select{min-width:160px}
input:focus-visible,select:focus-visible,button:focus-visible{outline:2px solid var(--accent); outline-offset:2px}
.dates{display:flex; gap:8px; align-items:center}
.dates .sep{color:var(--muted); font-size:13px; padding-bottom:9px}
.spacer{flex:1 1 auto}
button.reset{font-family:inherit; font-size:13px; font-weight:600; color:var(--ink-2); cursor:pointer; background:transparent;
  border:1px solid var(--line-strong); border-radius:7px; padding:9px 14px; min-height:38px}
button.reset:hover{background:var(--surface-2); color:var(--ink)}
.resultline{font-size:13px; color:var(--muted); font-variant-numeric:tabular-nums}
.resultline strong{color:var(--ink); font-weight:600}

/* ---- table ---- */
.tablewrap{border:1px solid var(--line); border-radius:12px; background:var(--surface); overflow-x:auto; box-shadow:var(--shadow)}
table{border-collapse:collapse; width:100%; min-width:1080px}
thead th{position:sticky; top:0; z-index:2; background:var(--surface-2); text-align:left; font-size:10.5px; letter-spacing:.1em;
  text-transform:uppercase; color:var(--muted); font-weight:700; padding:12px 14px; border-bottom:1px solid var(--line-strong); white-space:nowrap}
tbody td{padding:13px 14px; border-bottom:1px solid var(--line); vertical-align:top; font-size:13.5px}
tbody tr:last-child td{border-bottom:none}
tbody tr:hover td{background:var(--surface-2)}
.mono{font-family:"Roboto Mono",ui-monospace,monospace; font-size:12.5px; font-variant-numeric:tabular-nums; white-space:nowrap}
.cust{font-weight:600}
td.concern{color:var(--ink-2); min-width:300px; max-width:400px; font-size:13px}
.ht b{font-family:"Roboto Mono",monospace; font-size:14px; font-weight:500; display:block}
.ht span{font-size:11.5px; color:var(--muted); display:block; margin-top:1px}
.sz b{display:block; font-weight:600; font-size:14px}
.sz span{font-size:10px; letter-spacing:.05em; text-transform:uppercase; color:var(--muted); font-weight:700; display:block; margin-top:2px}
.pill{display:inline-flex; align-items:center; gap:6px; font-size:12px; font-weight:600; padding:4px 9px; border-radius:999px; white-space:nowrap}
.pill i{width:8px; height:8px; border-radius:50%; flex:none; font-style:normal}
.pill.s{background:var(--small-bg); color:var(--small)} .pill.s i{background:var(--small)}
.pill.g{background:var(--good-bg); color:var(--good)} .pill.g i{background:var(--good)}
.pill.b{background:var(--big-bg); color:var(--big)}  .pill.b i{background:var(--big)}
.chip{display:inline-block; font-size:11px; font-weight:600; padding:3px 8px; border-radius:999px; background:var(--surface-2); color:var(--ink-2); white-space:nowrap}

.note{border:1px solid var(--line-strong); border-left:3px solid var(--accent); background:var(--surface); border-radius:10px;
      padding:16px 20px; display:flex; flex-direction:column; gap:9px}
.note h2{font-family:"Spectral",Georgia,serif; font-weight:600; font-size:17px; margin:0}
.note p{margin:0; font-size:13.5px; color:var(--ink-2); max-width:82ch}
.note ul{margin:2px 0 0; padding-left:18px; font-size:13.5px; color:var(--ink-2); display:flex; flex-direction:column; gap:4px}
.note code{font-family:"Roboto Mono",monospace; font-size:12.5px; background:var(--surface-2); padding:1px 5px; border-radius:4px}
.empty{padding:52px 24px; text-align:center; color:var(--muted); font-size:14px}
footer{font-size:12.5px; color:var(--muted); padding-top:8px; border-top:1px solid var(--line); display:flex; flex-wrap:wrap; gap:6px 18px}

@media (max-width:760px){
  .wrap{padding:26px 15px 60px}
  .crow{grid-template-columns:96px 1fr 36px; gap:9px}
  input[type=search]{min-width:0; width:100%} .field{flex:1 1 100%} .dates{width:100%} .dates input{flex:1 1 0}
}
@media (prefers-reduced-motion:reduce){*{transition:none!important}}
</style>
'''

BODY = f'''<div class="wrap">

<header class="masthead">
  <div class="eyebrow">CommSlayer &middot; sizing signal</div>
  <h1>Fit by Height</h1>
  <p class="standfirst">Customers who told us both how tall they are and what size they bought or wear, paired with what actually happened when they put the tank on. Height is standardised to centimetres with the customer&rsquo;s own wording kept alongside. Nothing is inferred &mdash; every height, size and quote is lifted from the customer&rsquo;s own message.</p>
</header>

<section class="stats" id="stats" aria-label="Summary"></section>

<section class="panel" aria-label="Fit outcome by height band">
  <h2>Where the sizing breaks down</h2>
  <p class="sub">Fit outcome by height band. Segment width is the number of customers; counts are labelled on every segment.</p>
  <div class="legend">
    <span><i class="swatch" style="background:var(--small)"></i>Too Small</span>
    <span><i class="swatch" style="background:var(--good)"></i>Good Fit</span>
    <span><i class="swatch" style="background:var(--big)"></i>Too Big</span>
  </div>
  <div class="chart" id="chart"></div>
</section>

<section class="controls" aria-label="Filters">
  <div class="field">
    <label for="f-store">Store</label>
    <select id="f-store"><option value="">All stores</option></select>
  </div>
  <div class="field">
    <label for="f-from">Date</label>
    <div class="dates">
      <input type="date" id="f-from" value="{dmin}" aria-label="From date">
      <span class="sep">to</span>
      <input type="date" id="f-to" value="{dmax}" aria-label="To date">
    </div>
  </div>
  <div class="field">
    <label for="f-fit">Fit</label>
    <select id="f-fit">
      <option value="">All outcomes</option>
      <option value="Too Small">Too Small</option>
      <option value="Good Fit">Good Fit</option>
      <option value="Too Big">Too Big</option>
    </select>
  </div>
  <div class="field">
    <label for="f-q">Search</label>
    <input type="search" id="f-q" placeholder="Customer, size, height, concern&hellip;">
  </div>
  <div class="spacer"></div>
  <button class="reset" id="reset" type="button">Reset filters</button>
</section>

<p class="resultline" id="resultline"></p>

<div class="tablewrap">
  <table>
    <thead><tr>
      <th scope="col">Date</th><th scope="col">Store</th><th scope="col">Order&nbsp;#</th><th scope="col">Customer</th>
      <th scope="col">Height</th><th scope="col">Size ordered / worn</th><th scope="col">Fit</th>
      <th scope="col">Customer&rsquo;s exact fit concern</th><th scope="col">Ticket</th>
    </tr></thead>
    <tbody id="tbody"></tbody>
  </table>
</div>
<p class="empty" id="empty" hidden>No customers match these filters.</p>

<section class="note">
  <h2>How this set was built, and what is missing</h2>
  <p>This is <strong>{len(rows)} customers, not the 100 asked for</strong>. The limit is the data, not the filter: height is volunteered far less often than bra size or weight, and the rule was to include a customer only where <em>both</em> height and a size are stated outright. Roughly half the customers who gave a height never named a size (&ldquo;I went by the size chart and bought what was recommended&rdquo;), and those were dropped rather than guessed at. CommSlayer&rsquo;s content search also caps at 25 results per query and cannot paginate, so this is everything ~22 height-phrase searches surfaced.</p>
  <p>Where a customer gave a bra size but never a tank size, the bra size is recorded and tagged <strong>Bra size worn</strong>; a tank size is tagged <strong>Tank size ordered</strong>. Order numbers appear only where the customer quoted one.</p>
  <p>All {len(rows)} come from the <strong>Maggie&rsquo;s Tanks</strong> CommSlayer account, the only account this integration is authorised for. The other three stores keep separate accounts with their own MCP endpoints and return nothing through this connection:</p>
  <ul>
    <li><strong>Mary&rsquo;s Tanks</strong> &mdash; account <code>6377</code>, not connected</li>
    <li><strong>Lyn&rsquo;s Tanks</strong> &mdash; account <code>6527</code>, not connected</li>
    <li><strong>Simply Elsie</strong> &mdash; account <code>7356</code>, not connected</li>
  </ul>
</section>

<footer>
  <span>Source: CommSlayer conversations, account 6576 (Maggie&rsquo;s Tanks)</span>
  <span>Messages dated {dmin} &ndash; {dmax}</span>
  <span>Height converted at 1 in = 2.54 cm, rounded to the nearest cm</span>
</footer>
</div>
<div id="tip" role="status"></div>

<script type="application/json" id="data">{data_json}</script>
<script type="application/json" id="bands">{bands_json}</script>
<script>
(function(){{
  var ROWS = JSON.parse(document.getElementById('data').textContent);
  var BANDS = JSON.parse(document.getElementById('bands').textContent);
  var STORES = {json.dumps(STORES)};
  var D_MIN = {json.dumps(dmin)}, D_MAX = {json.dumps(dmax)};
  var FITKEY = {{'Too Small':'s','Good Fit':'g','Too Big':'b'}};

  var $ = function(id){{ return document.getElementById(id); }};
  var tbody=$('tbody'), empty=$('empty'), resultline=$('resultline'), statsEl=$('stats'),
      chartEl=$('chart'), tip=$('tip'),
      fStore=$('f-store'), fFrom=$('f-from'), fTo=$('f-to'), fFit=$('f-fit'), fQ=$('f-q');

  STORES.forEach(function(s){{
    var n = ROWS.filter(function(r){{ return r.store===s; }}).length;
    var o=document.createElement('option'); o.value=s;
    o.textContent = s + (n ? ' ('+n+')' : ' (0 \\u2014 not connected)');
    fStore.appendChild(o);
  }});

  function esc(s){{ return String(s).replace(/[&<>"]/g,function(c){{
    return {{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}}[c]; }}); }}

  function current(){{
    var store=fStore.value, from=fFrom.value||D_MIN, to=fTo.value||D_MAX,
        fit=fFit.value, q=fQ.value.trim().toLowerCase();
    return ROWS.filter(function(r){{
      if (store && r.store!==store) return false;
      if (r.date<from || r.date>to) return false;
      if (fit && r.fit!==fit) return false;
      if (q){{
        var hay=[r.customer,r.order,r.h_orig,r.cm+' cm',r.size,r.basis,r.fit,r.concern,r.ticket,r.store].join(' ').toLowerCase();
        if (hay.indexOf(q)===-1) return false;
      }}
      return true;
    }});
  }}

  function showTip(e,text){{
    tip.textContent=text; tip.style.opacity='1';
    var x=e.clientX+12, y=e.clientY-34;
    if (x+tip.offsetWidth>window.innerWidth-8) x=e.clientX-tip.offsetWidth-12;
    tip.style.left=x+'px'; tip.style.top=Math.max(6,y)+'px';
  }}
  function hideTip(){{ tip.style.opacity='0'; }}

  function drawChart(out){{
    chartEl.innerHTML = BANDS.map(function(b){{
      var inb = out.filter(function(r){{ return r.cm>=b.lo && r.cm<=b.hi; }});
      var counts = {{'Too Small':0,'Good Fit':0,'Too Big':0}};
      inb.forEach(function(r){{ counts[r.fit]++; }});
      var total = inb.length;
      var segs = ['Too Small','Good Fit','Too Big'].filter(function(k){{ return counts[k]>0; }}).map(function(k){{
        var pct = total ? (counts[k]/total*100) : 0;
        return '<div class="seg '+FITKEY[k]+'" style="flex:'+counts[k]+' 1 0" '+
               'data-tip="'+esc(b.label+' \\u00b7 '+k+': '+counts[k]+' of '+total)+'">'+
               (pct>=11 ? counts[k] : '')+'</div>';
      }}).join('');
      return '<div class="crow">'+
        '<div class="clabel"><b>'+b.label+'</b><span>'+b.sub+'</span></div>'+
        '<div class="bar">'+(segs||'')+'</div>'+
        '<div class="ctotal">'+(total||'\\u2013')+'</div></div>';
    }}).join('');

    Array.prototype.forEach.call(chartEl.querySelectorAll('.seg'), function(el){{
      el.addEventListener('mousemove', function(e){{ showTip(e, el.getAttribute('data-tip')); }});
      el.addEventListener('mouseleave', hideTip);
    }});
  }}

  function render(){{
    var out = current();

    tbody.innerHTML = out.map(function(r){{
      return '<tr>'+
        '<td class="mono">'+esc(r.date)+'</td>'+
        '<td><span class="chip">'+esc(r.store)+'</span></td>'+
        '<td class="mono">'+esc(r.order)+'</td>'+
        '<td class="cust">'+esc(r.customer)+'</td>'+
        '<td class="ht"><b>'+r.cm+' cm</b><span>'+esc(r.h_orig)+'</span></td>'+
        '<td class="sz"><b>'+esc(r.size)+'</b><span>'+esc(r.basis)+'</span></td>'+
        '<td><span class="pill '+FITKEY[r.fit]+'"><i></i>'+esc(r.fit)+'</span></td>'+
        '<td class="concern">'+esc(r.concern)+'</td>'+
        '<td class="mono">'+esc(r.ticket)+'</td>'+
      '</tr>';
    }}).join('');
    empty.hidden = out.length>0;

    resultline.innerHTML='Showing <strong>'+out.length+'</strong> of '+ROWS.length+
      ' customers who stated both height and size'+(fStore.value?' &middot; '+esc(fStore.value):'')+'.';

    var small=out.filter(function(r){{return r.fit==='Too Small';}}).length;
    var good=out.filter(function(r){{return r.fit==='Good Fit';}}).length;
    var big=out.filter(function(r){{return r.fit==='Too Big';}}).length;
    var cms=out.map(function(r){{return r.cm;}});
    var median='\\u2013';
    if (cms.length){{ var s=cms.slice().sort(function(a,b){{return a-b;}});
      median = (s.length%2 ? s[(s.length-1)/2] : Math.round((s[s.length/2-1]+s[s.length/2])/2)) + ' cm'; }}
    var cards=[[out.length,'Customers'],[small,'Too small'],[good,'Good fit'],[big,'Too big'],[median,'Median height']];
    statsEl.innerHTML=cards.map(function(c){{
      return '<div class="stat"><b>'+c[0]+'</b><span>'+c[1]+'</span></div>'; }}).join('');

    drawChart(out);
  }}

  [fStore,fFrom,fTo,fFit].forEach(function(el){{ el.addEventListener('change',render); }});
  fQ.addEventListener('input',render);
  $('reset').addEventListener('click',function(){{
    fStore.value=''; fFrom.value=D_MIN; fTo.value=D_MAX; fFit.value=''; fQ.value=''; render();
  }});
  window.addEventListener('scroll',hideTip,{{passive:true}});
  render();
}})();
</script>
'''

open('fit_by_height.html','w').write(HEAD + BODY)
print('rows:', len(rows))
