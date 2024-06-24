import os
import json
import requests
from datetime import datetime, timedelta

def calculate_dates(day_of_month):
    today = datetime.now()
    current_year = today.year
    current_month = today.month
    next_month = current_month + 1 if current_month < 12 else 1
    next_month_year = current_year if current_month < 12 else current_year + 1

    if today.day < day_of_month:
        start_date = datetime(current_year, current_month, day_of_month)
    else:
        start_date = datetime(next_month_year, next_month, day_of_month)

    end_date = datetime(start_date.year, start_date.month, day_of_month) - timedelta(days=1)
    task_creation_date = start_date - timedelta(days=7)

    return task_creation_date, start_date, end_date

def get_tasks_with_conditions(list_id, custom_field_id, status_id, access_token):
    url = f"https://api.clickup.com/api/v2/list/{list_id}/task?include_custom_fields=true"
    headers = {
        'Authorization': access_token,
        'Content-Type': 'application/json'
    }
    
    response = requests.get(url, headers=headers)
    tasks_to_create = []
    if response.status_code == 200:
        tasks = response.json().get('tasks', [])
        for task in tasks:
            if task['status']['id'] == status_id:
                for field in task.get('custom_fields', []):
                    if field['id'] == custom_field_id and field.get('value'):
                        day_of_month = int(field['value'])
                        task_creation_date, start_date, end_date = calculate_dates(day_of_month)
                        if task_creation_date.date() == datetime.now().date():
                            tasks_to_create.append((task, start_date, end_date))
    else:
        print(f"Failed to retrieve tasks: {response.status_code}")

    return tasks_to_create

def create_task(title, list_id, access_token, due_date):
    url = f"https://api.clickup.com/api/v2/list/{list_id}/task"
    headers = {
        'Authorization': access_token,
        'Content-Type': 'application/json'
    }

    # Setting the due date to the end of the day
    due_date_end_of_day = datetime.combine(due_date, datetime.max.time())
    due_timestamp = int(due_date_end_of_day.timestamp() * 1000)  # Convert to milliseconds

    data = {
        "name": title,
        "description": "Automatically created task for billing period.",
        "due_date": due_timestamp
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        print("Task created successfully:", title)
    else:
        print("Failed to create task:", response.status_code, response.text)

# Load the API Key
access_token = os.getenv('CLICKUP_API_KEY') or json.load(open('credentials.json'))['CLICKUP_API_KEY']

list_id = "42370637"
destination_list_id = "901201953178"
status_id = "sc42370637_Zea9lI9k"
custom_field_id = "dcd50ff8-4bed-4df2-a59b-3ce491837ae3"

tasks_to_create = get_tasks_with_conditions(list_id, custom_field_id, status_id, access_token)
for task, start_date, end_date in tasks_to_create:
    title = f"{start_date.strftime('%Y-%m-%d')} - {end_date.strftime('%Y-%m-%d')}, {task['name']}"
    # Assuming today is the task creation date and also the due date
    create_task(title, destination_list_id, access_token, datetime.now().date())
