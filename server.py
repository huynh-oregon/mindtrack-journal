#!/usr/bin/env python3
import os, json, uuid, re
from datetime import datetime, timezone
from flask import Flask, jsonify, request, render_template, send_from_directory
from typing import Optional
import requests

# Microservice base URLs (override with env vars if needed)
A = os.getenv("A_URL", "http://localhost:5000")  # A: /count-words
B = os.getenv("B_URL", "http://localhost:5001")  # B: /list, /random
C = os.getenv("C_URL", "http://localhost:5002")  # C: /count, /count-with-date
D = os.getenv("D_URL", "http://localhost:5003")  # D: /export/csv, /export/json
TIMEOUT = 4  # seconds

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(ROOT, "data", "entries")
EXPORT_DIR = os.path.join(ROOT, "exports")
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(EXPORT_DIR, exist_ok=True)

app = Flask(__name__, static_folder="static", template_folder="templates")

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")       # YYYY-MM-DD
TIME_RE = re.compile(r"^\d{2}:\d{2}$")             # HH:MM (24h)

def http(method, url, **kw):
    """HTTP helper that returns (status_code, body). Never raises."""
    try:
        r = requests.request(method, url, timeout=TIMEOUT, **kw)
        if "application/json" in (r.headers.get("content-type") or ""):
            body = r.json()
        else:
            body = r.text
        return r.status_code, body
    except requests.exceptions.RequestException as e:
        return 503, {"error": "service_unavailable", "detail": str(e), "target": url}

def _entry_path(eid: str) -> str:
    return os.path.join(DATA_DIR, f"{eid}.json")


def _read_entry(eid: str) -> Optional[dict]:
    path = _entry_path(eid)
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def _write_entry(e: dict):
    eid = e.get("id")
    if not eid:
        raise ValueError("entry missing id")
    path = _entry_path(eid)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(e, f, ensure_ascii=False)
    os.replace(tmp, path)
# --- delete helper (Python 3.9 friendly) ---
def _delete_entry(eid):
    path = _entry_path(eid)
    if not os.path.exists(path):
        return False
    try:
        os.remove(path)
        return True
    except Exception:
        return False
def _list_entries() -> list[dict]:
    items = []
    for name in os.listdir(DATA_DIR):
        if not name.endswith(".json"):
            continue
        p = os.path.join(DATA_DIR, name)
        try:
            with open(p, "r", encoding="utf-8") as f:
                e = json.load(f)
            e["_file"] = name
            items.append(e)
        except Exception:
            continue
    # sort by date+time desc (fallbacks if missing)
    def key(e):
        d = str(e.get("date", "0000-00-00"))
        t = str(e.get("time", "00:00"))
        return (d, t)
    items.sort(key=key, reverse=True)
    return items

@app.get("/")
def home():
    return render_template("index.html")

# ---------- Entries (local) ----------
@app.post("/api/entries/create")
def create_entry():
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    encouragement = (data.get("encouragement") or "").strip()
    # Allow text OR encouragement (or both). Reject only if both empty.
    if not text and not encouragement:
        return jsonify({"ok": False, "error": "empty_entry"}), 400

    # Date & time (optional). If provided, light validation; else default now (UTC).
    date_s = (data.get("date") or "").strip()
    time_s = (data.get("time") or "").strip()
    now = datetime.now(timezone.utc)
    if not date_s or not DATE_RE.match(date_s):
        date_s = now.date().isoformat()
    if time_s and not TIME_RE.match(time_s):
        return jsonify({"ok": False, "error": "invalid_time_format (HH:MM)"}), 400
    if not time_s:
        time_s = now.strftime("%H:%M")

    eid = uuid.uuid4().hex
    entry = {"id": eid, "date": date_s, "time": time_s}
    if text: entry["text"] = text
    if encouragement: entry["encouragement"] = encouragement

    _write_entry(entry)
    return jsonify({"ok": True, "id": eid, "path": _entry_path(eid)}), 200

@app.get("/api/entries/list")
def entries_list():
    items = _list_entries()
    # shallow previews for UI
    out = []
    for e in items[:100]:
        preview = (e.get("text") or e.get("encouragement") or "")[:80]
        out.append({
            "id": e.get("id"), "date": e.get("date"), "time": e.get("time"),
            "preview": preview
        })
    return jsonify({"count": len(items), "items": out}), 200

@app.get("/api/entries/get")
def entries_get():
    eid = (request.args.get("id") or "").strip()
    e = _read_entry(eid)
    if not e:
        return jsonify({"ok": False, "error": "not_found"}), 404
    return jsonify({"ok": True, "entry": e}), 200

@app.post("/api/entries/update")
def entries_update():
    data = request.get_json(silent=True) or {}
    eid = (data.get("id") or "").strip()
    if not eid:
        return jsonify({"ok": False, "error": "missing_id"}), 400
    e = _read_entry(eid)
    if not e:
        return jsonify({"ok": False, "error": "not_found"}), 404

    # Update fields if provided
    if "text" in data:
        text = (data.get("text") or "").strip()
        if text:
            e["text"] = text
        else:
            e.pop("text", None)  
    if "encouragement" in data:
        enc = (data.get("encouragement") or "").strip()
        if enc:
            e["encouragement"] = enc
        else:
            e.pop("encouragement", None)

    if "date" in data:
        date_s = (data.get("date") or "").strip()
        if date_s and DATE_RE.match(date_s):
            e["date"] = date_s
        else:
            return jsonify({"ok": False, "error": "invalid_date_format (YYYY-MM-DD)"}), 400

    if "time" in data:
        time_s = (data.get("time") or "").strip()
        if time_s and TIME_RE.match(time_s):
            e["time"] = time_s
        else:
            return jsonify({"ok": False, "error": "invalid_time_format (HH:MM)"}), 400

    # Must keep at least one of text/encouragement
    if not e.get("text") and not e.get("encouragement"):
        return jsonify({"ok": False, "error": "entry_cannot_be_empty"}), 400

    _write_entry(e)
    return jsonify({"ok": True, "entry": e}), 200

@app.post("/api/entries/delete")
def entries_delete():
    data = request.get_json(silent=True) or {}
    eid = (data.get("id") or "").strip()
    if not eid:
        return jsonify({"ok": False, "error": "missing_id"}), 400
    if not _read_entry(eid):
        return jsonify({"ok": False, "error": "not_found"}), 404
    ok = _delete_entry(eid)
    if not ok:
        return jsonify({"ok": False, "error": "delete_failed"}), 500
    return jsonify({"ok": True, "id": eid}), 200


# ---------- A ----------
@app.post("/api/a/wordcount")
def api_a_wordcount():
    data = request.get_json(silent=True) or {}
    code, body = http("POST", f"{A}/count-words", json={"text": data.get("text", "")})
    return (jsonify(body), code)

# ---------- B (Encouragements) ----------
@app.get("/api/b/list")
def api_b_list():
    code, body = http("GET", f"{B}/list")
    return (jsonify(body), code)

@app.get("/api/b/random")
def api_b_random():
    code, body = http("GET", f"{B}/random")
    return (jsonify(body), code)

# ---------- C ----------
@app.get("/api/c/count")
def api_c_count():
    code, body = http("GET", f"{C}/count")
    return (jsonify(body), code)

@app.get("/api/c/count-with-date")
def api_c_count_with_date():
    code, body = http("GET", f"{C}/count-with-date")
    return (jsonify(body), code)

# ---------- D ----------
@app.post("/api/d/export-csv")
def api_d_export_csv():
    code, body = http("POST", f"{D}/export/csv")
    if code == 204:
        return jsonify({"ok": True, "note": "no entries"}), 200
    return (jsonify(body), code)


# Exported files 
@app.get("/exports/<path:filename>")
def serve_exports(filename):
    return send_from_directory(EXPORT_DIR, filename, as_attachment=False)

if __name__ == "__main__":
    # Visit http://localhost:8080
    app.run(host="0.0.0.0", port=8080)
