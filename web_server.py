
from flask import Flask, render_template, jsonify
import datetime
import json
import os

app = Flask(__name__)

DATA_DIR = "data"

@app.route('/')
def dashboard():
    with open(os.path.join(DATA_DIR, 'v31_status.json'), ' 'r') as f:
        status = json.load(f)
    with open(os.path.join(DATA_DIR, 'capital_trend.json'), 'r') as f:
        capital_trend = json.load(f)
    return render_template('index.html', status=status, capital_trend=capital_trend)

@app.route('/v31_status.json')
def v31_status():
    return jsonify(json.load(open(os.path.join(DATA_DIR, 'v31_status.json'))))

@app.route('/capital_trend.json')
def capital_trend():
    return jsonify(json.load(open(os.path.join(DATA_DIR, 'capital_trend.json'))))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
