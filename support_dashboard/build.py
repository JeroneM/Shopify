import json, pathlib
HERE = pathlib.Path(__file__).parent
data = (HERE/"data"/"dashboard_data.json").read_text()
tpl = (HERE/"template.html").read_text()
assert "/*__DATA__*/" in tpl
(HERE/"dashboard.html").write_text(tpl.replace("/*__DATA__*/", data))
print("dashboard.html", len((HERE/"dashboard.html").read_text()), "bytes")
