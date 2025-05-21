import json
import os

DATA_PATH = "data"

def ensure_data_path():
    if not os.path.exists(DATA_PATH):
        os.makedirs(DATA_PATH)

def update_json(file, record):
    """
    將單筆紀錄 append 到指定 JSON 檔案中
    """
    ensure_data_path()
    path = os.path.join(DATA_PATH, file)
    if os.path.exists(path):
        with open(path, "r") as f:
            data = json.load(f)
    else:
        data = []
    data.append(record)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def reset_data_files():
    """
    重置所有 JSON 檔案為空清單（用於重新回測）
    """
    for file in ["trade_records.json", "capital_trend.json"]:
        with open(os.path.join(DATA_PATH, file), "w") as f:
            json.dump([], f, indent=2)
