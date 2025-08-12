from flask import Flask, jsonify
from datetime import datetime
import random

app = Flask(__name__)

ENCOURAGEMENTS = [
    "You’ve got this.",
    "Small steps count.",
    "Keep going—progress over perfection.",
    "Be kind to yourself today.",
    "One page today is a chapter tomorrow.",
    "Breathe. Reset. Try again.",
    "Your effort matters.",
    "You’re doing better than you think.",
    "Focus on what you can control.",
    "Show up for yourself."
]

@app.get("/list")
def list_all():
    return jsonify({"count": len(ENCOURAGEMENTS), "items": ENCOURAGEMENTS}), 200

@app.get("/random")
def random_one():
    return jsonify({"encouragement": random.choice(ENCOURAGEMENTS)}), 200

if __name__ == "__main__":
    # Runs on http://localhost:5001
    app.run(host="0.0.0.0", port=5001)
