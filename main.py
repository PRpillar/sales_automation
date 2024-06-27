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

    end_date = start_date + relativedelta(months=1) - timedelta(days=1)
    task_creation_date = start_date - timedelta(days=7)

    return task_creation_date, start_date, end_date

def get_tasks_with_conditions(list_id, custom_field_id, status_id, access_token, motherbrand_field_id):
    url = f"https://api.clickup.com/api/v2/list/{list_id}/task?include_custom_fields=true"
    headers = {
        'Authorization': access_token,
        'Content-Type': 'application/json'
    }
    
    response = requests.get(url, headers=headers)
    parent_tasks = {}
    independent_tasks = []

    if response.status_code == 200:
        tasks = response.json().get('tasks', [])
        all_tasks_dict = {task['id']: task for task in tasks}  # Dictionary to access task details by ID

        for task in tasks:
            if task['status']['id'] == status_id:
                day_of_month = None
                parent_id = None
                for field in task.get('custom_fields', []):
                    if field['id'] == custom_field_id and field.get('value'):
                        day_of_month = int(field['value'])
                    if field['id'] == motherbrand_field_id and field.get('value'):
                        parent_id = field['value'][0]['id']
                
                if day_of_month:
                    task_creation_date, start_date, end_date = calculate_dates(day_of_month)
                    if task_creation_date.date() == datetime.now().date():
                        if parent_id:
                            if parent_id not in parent_tasks:
                                parent_tasks[parent_id] = {
                                    'start_date': start_date, 
                                    'end_date': end_date, 
                                    'child_names': [task['name']],
                                    'parent_name': all_tasks_dict[parent_id]['name']  # Use parent name from task dictionary
                                }
                            else:
                                parent_tasks[parent_id]['child_names'].append(task['name'])
                        elif not parent_id:  # This is an independent task or a parent without children yet recorded
                            independent_tasks.append((task, start_date, end_date))
    else:
        print(f"Failed to retrieve tasks: {response.status_code}")
    
    # Remove independent parent tasks that have children aggregated
    final_independent_tasks = [task for task in independent_tasks if task[0]['id'] not in parent_tasks]
    return parent_tasks, final_independent_tasks


def create_task(title, list_id, access_token, due_date):
    url = f"https://api.clickup.com/api/v2/list/{list_id}/task"
    headers = {
        'Authorization': access_token,
        'Content-Type': 'application/json'
    }

    moscow_time = timezone(timedelta(hours=3))
    due_date = datetime.combine(due_date, datetime.min.time()).astimezone(moscow_time)
    due_timestamp = int(due_date.timestamp() * 1000)

    data = {
        "name": title,
        "description": "Automatically created task for billing period.",
        "due_date": due_timestamp
    }

    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        new_task_id = response.json().get('id')
        print(f"Task created successfully: {title}, ID: {new_task_id}")
        return new_task_id
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

    response = requests.post(url, json=payload, headers=headers)
    if response.status_code in [200, 201]:
        print("Task relationship updated successfully.")
    else:
        print(f"Failed to update task relationship: {response.status_code} {response.text}")


# Main execution
access_token = os.getenv('CLICKUP_API_KEY') or json.load(open('credentials.json'))['CLICKUP_API_KEY']
list_id = "42370637"
destination_list_id = "901201953178"
status_id = "sc42370637_Zea9lI9k"
custom_field_id = "dcd50ff8-4bed-4df2-a59b-3ce491837ae3"
relationship_field_id = '29aafb0f-2e62-4425-b409-5f21538b3c3c' 
motherbrand_field_id = '65152352-2245-4e01-a375-06f7094abc53'

parent_tasks, independent_tasks = get_tasks_with_conditions(list_id, custom_field_id, status_id, access_token, motherbrand_field_id)

# Create tasks for independent and parent brands
for task_info in independent_tasks:
    task, start_date, end_date = task_info
    title = f"{start_date.strftime('%Y-%m-%d')} - {end_date.strftime('%Y-%m-%d')}, {task['name']}"
    new_task_id = create_task(title, destination_list_id, access_token, datetime.now().date())
    if new_task_id:
        set_relationship_field(new_task_id, relationship_field_id, access_token, add_ids=[task['id']])

for parent_id, info in parent_tasks.items():
    title = f"{info['start_date'].strftime('%Y-%m-%d')} - {info['end_date'].strftime('%Y-%m-%d')}, {info['parent_name']} + " + " + ".join(info['child_names'])
    new_task_id = create_task(title, destination_list_id, access_token, datetime.now().date())
    if new_task_id:
        set_relationship_field(new_task_id, relationship_field_id, access_token, add_ids=[parent_id])
