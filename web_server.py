from flask import Flask, render_template
import json
import os

app = Flask(__name__)

@app.route('/')
def index():
    try:
        with open('date/v31_status.json', 'r', encoding='utf-8') as f:
            status = json.load(f)
    except:
        status = []

    try:
        with open('date/v31_status_history.json', 'r', encoding='utf-8') as f:
            status_history = json.load(f)
    except:
        status_history = []

    try:
        with open('date/capital_trend.json', 'r', encoding='utf-8') as f:
            capital_trend = json.load(f)
    except:
        capital_trend = []

    return render_template('V31.6_Web_Dashboard.html',
                           status=status,
                           status_history=status_history,
                           capital_trend=capital_trend)
