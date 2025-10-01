import json
import os
from datetime import datetime

def update_sensor_data_mock():
    file_path = os.path.join(os.path.dirname(__file__), 'plant_data.json')
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Read existing data or initialize if file is empty/invalid
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        data = []

    # Append new dummy data
    new_data = {
        "timestamp": current_time,
        "temperature": 25.0 + (datetime.now().second % 10) - 5, # Simulate slight variation
        "humidity": 60.0 + (datetime.now().minute % 5) - 2,
        "soil_moisture": 150 + (datetime.now().hour % 20) - 10,
        "motion_detected": "YES" if datetime.now().second % 2 == 0 else "NO",
        "pump_state": "ON" if datetime.now().minute % 3 == 0 else "OFF"
    }
    data.append(new_data)

    # Keep only the last 10 entries to prevent file from growing too large
    data = data[-10:]

    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)

if __name__ == '__main__':
    update_sensor_data_mock() 