from flask import Flask, send_from_directory
import os

app = Flask(__name__)

@app.route('/')
def serve_dashboard():
    return send_from_directory('.', 'V31.6_Web_Dashboard.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('.', filename)

if __name__ == '__main__':
    # 讓區網內其他裝置（例如手機）也可以開啟此網頁
    app.run(host='0.0.0.0', port=8080)
