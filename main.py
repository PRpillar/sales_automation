import os
import json
import requests
from datetime import datetime, timedelta, timezone
from dateutil.relativedelta import relativedelta

def calculate_dates(day_of_month):
    today = datetime.now(timezone.utc)  # Ensuring the script uses UTC
    current_year = today.year
    current_month = today.month
    next_month = current_month + 1 if current_month < 12 else 1
    next_month_year = current_year if current_month < 12 else current_year + 1

    if today.day < day_of_month:
        start_date = datetime(current_year, current_month, day_of_month, tzinfo=timezone.utc)
    else:
        start_date = datetime(next_month_year, next_month, day_of_month, tzinfo=timezone.utc)

    # Calculate the end date by adding one month and then subtracting one day
    end_date = start_date + relativedelta(months=1) - timedelta(days=1)

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

    moscow_time = timezone(timedelta(hours=3))
    due_date = datetime.combine(due_date, datetime.min.time()).astimezone(moscow_time)
    due_timestamp = int(due_date.timestamp() * 1000)  # Convert to milliseconds

    data = {
        "name": title,
        "description": "Automatically created task for billing period.",
        "due_date": due_timestamp
    }

    print(f"Creating task with data: {data}")  # Debug: Show task creation data

    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        new_task_id = response.json().get('id')
        print(f"Task created successfully: {title}, ID: {new_task_id}")
        return new_task_id  # Return the new task ID for linking
    else:
        print(f"Failed to create task: {response.status_code} {response.text}")
        return None


def set_relationship_field(task_id, field_id, access_token, add_ids=None, remove_ids=None):
    url = f"https://api.clickup.com/api/v2/task/{task_id}/field/{field_id}"

    headers = {
        "Content-Type": "application/json",
        "Authorization": access_token
    }

    value_payload = {}
    if add_ids:
        value_payload['add'] = add_ids
    if remove_ids:
        value_payload['rem'] = remove_ids

    payload = {
        "value": value_payload
    }

    print(f"Updating task {task_id} with relationship field {field_id} and payload: {payload}")  # Debug: Show update data

    response = requests.post(url, json=payload, headers=headers)
    if response.status_code in [200, 201]:
        print("Task relationship updated successfully.")
        data = response.json()
        print(data)
    else:
        print(f"Failed to update task relationship: {response.status_code} {response.text}")     


# Load the API Key
access_token = os.getenv('CLICKUP_API_KEY') or json.load(open('credentials.json'))['CLICKUP_API_KEY']

list_id = "42370637"
destination_list_id = "901201953178"
status_id = "sc42370637_Zea9lI9k"
custom_field_id = "dcd50ff8-4bed-4df2-a59b-3ce491837ae3"
relationship_field_id = '29aafb0f-2e62-4425-b409-5f21538b3c3c' 


tasks_to_create = get_tasks_with_conditions(list_id, custom_field_id, status_id, access_token)
for task_info in tasks_to_create:
    original_task, start_date, end_date = task_info
    title = f"{start_date.strftime('%Y-%m-%d')} - {end_date.strftime('%Y-%m-%d')}, {original_task['name']}"

    # Create the new task and get the new task ID
    new_task_id = create_task(title, destination_list_id, access_token, datetime.now().date())

    # If task creation was successful, set the relationship
    if new_task_id:
        add_ids = [original_task['id']]  # List of task IDs to link to, could be more than one
        set_relationship_field(new_task_id, relationship_field_id, access_token, add_ids=add_ids)
