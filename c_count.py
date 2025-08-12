import os
from datetime import datetime, timezone
from flask import Flask, jsonify

DATA_DIR = os.path.join("data", "entries")
os.makedirs(DATA_DIR, exist_ok=True)

app = Flask(__name__)

def _is_entry(name: str) -> bool:
    return name.endswith(".json") and os.path.isfile(os.path.join(DATA_DIR, name))

def _count() -> int:
    try:
        return sum(1 for n in os.listdir(DATA_DIR) if _is_entry(n))
    except FileNotFoundError:
        return 0

@app.get("/count")
def count_only():
    return jsonify({"count": _count()}), 200

@app.get("/count-with-date")
def count_with_date():
    today = datetime.now(timezone.utc).date().isoformat()
    return jsonify({"count": _count(), "date": today}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002)
