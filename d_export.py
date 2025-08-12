import os, json, csv, uuid
from io import StringIO
from datetime import datetime, timezone, date
from flask import Flask, request, jsonify

DATA_DIR = os.path.join("data", "entries")
EXPORT_DIR = "exports"
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(EXPORT_DIR, exist_ok=True)

app = Flask(__name__)

def _read_entries() -> list[dict]:
    out = []
    for name in os.listdir(DATA_DIR):
        if not name.endswith(".json"):
            continue
        p = os.path.join(DATA_DIR, name)
        try:
            with open(p, "r", encoding="utf-8") as f:
                out.append(json.load(f))
        except Exception:
            continue
    return out

def _atomic_write(path: str, content: str):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(content)
    os.replace(tmp, path)


@app.post("/export/csv")
def export_csv():
    entries = _read_entries()
    if not entries:
        return ("", 204)
    fname = f"entries_{datetime.now(timezone.utc).date().isoformat()}_{uuid.uuid4().hex[:8]}.csv"
    fpath = os.path.join(EXPORT_DIR, fname)

    header = ["id", "date", "text"]
    rows = [[str(e.get("id","")), str(e.get("date","")), str(e.get("text","")).replace("\n"," ").replace("\r"," ")]
            for e in entries]

    buf = StringIO()
    writer = csv.writer(buf, quoting=csv.QUOTE_MINIMAL)
    writer.writerow(header); writer.writerows(rows)
    _atomic_write(fpath, buf.getvalue())

    return jsonify({"format": "csv", "path": fpath}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5003)
