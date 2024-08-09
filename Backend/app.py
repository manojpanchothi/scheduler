from flask import Flask, request, jsonify
import pandas as pd
from flask_cors import CORS  # Import CORS

from datetime import datetime, timedelta
from googleapiclient.discovery import build
from google.oauth2 import service_account

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000"])
# Google Sheets API setup
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SERVICE_ACCOUNT_FILE = 'scheduler-432006-fb9d3c012656.json'

creds = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)
sheet_service = build('sheets', 'v4', credentials=creds)

SPREADSHEET_ID = '1Qw0PbPXggNkkizV5h_qbrQKT99DrhwQXbG3msNMhEfI'

# Example function to adjust timings based on AI predictions
def adjust_time(task_name, expected_time):
    # Placeholder AI adjustment logic
    adjustments = {
        "Study for Math test": 3,
        "Complete homework": 4,
        "Exercise": 1,
    }
    return adjustments.get(task_name, expected_time)

# Endpoint to create schedule
@app.route('/create-schedule', methods=['POST'])
def create_schedule():
    tasks = request.json['tasks']
    schedule = []
    start_time = datetime.strptime("08:00", "%H:%M")
    
    for task in tasks:
        # Ensure task['expected_time'] is a number
        expected_time = float(task['expected_time']) if '.' in str(task['expected_time']) else int(task['expected_time'])
        adjusted_time = adjust_time(task['task_name'], expected_time)
        
        # Convert adjusted_time to a float or int if necessary
        if isinstance(adjusted_time, str):
            adjusted_time = float(adjusted_time) if '.' in adjusted_time else int(adjusted_time)
        
        end_time = start_time + timedelta(hours=adjusted_time)
        
        detailed_plan = f"{task['description']}. Allocate focus time with breaks."
        remark = "Estimated time adjusted based on task complexity." if adjusted_time > expected_time else "Estimated time is accurate."
        
        schedule.append({
            "date": datetime.now().strftime("%Y-%m-%d"),
            "task_name": task['task_name'],
            "detailed_plan": detailed_plan,
            "timings": f"{start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}",
            "remarks": remark
        })
        
        start_time = end_time + timedelta(minutes=15)

    df = pd.DataFrame(schedule)
    export_to_google_sheets(df)

    return jsonify({"status": "success", "schedule": schedule})

# Function to export the schedule to Google Sheets
def export_to_google_sheets(df):
    sheet = sheet_service.spreadsheets()
    data = df.values.tolist()
    data.insert(0, df.columns.tolist())

    # Specify the range starting from A1
    range_name = 'Sheet1!A1'

    request = sheet.values().update(spreadsheetId=SPREADSHEET_ID, range=range_name,
                                    valueInputOption='RAW', body={'values': data})
    request.execute()


if __name__ == '__main__':
    app.run(debug=True)
