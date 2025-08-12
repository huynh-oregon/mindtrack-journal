from flask import Flask, request, jsonify

app = Flask(__name__)

@app.post("/count-words")
def count_words():
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    count = len(text.split()) if text else 0
    return jsonify({"count": count}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
