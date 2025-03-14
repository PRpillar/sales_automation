import os
import json
import requests

def get_tasks(list_id, access_token):
    """
    Retrieve tasks from the specified ClickUp list.
    """
    url = f"https://api.clickup.com/api/v2/list/{list_id}/task?include_custom_fields=true"
    headers = {
        'Authorization': access_token,
        'Content-Type': 'application/json'
    }
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Failed to retrieve tasks: {response.status_code} {response.text}")
        return []
    
    return response.json().get("tasks", [])

def print_task_details(task):
    """
    Print details for a single task, including all custom fields.
    """
    print(f"Task ID: {task.get('id')}")
    print(f"Task Name: {task.get('name')}")
    print(f"Status: {task.get('status', {}).get('status')}")
    print("Custom Fields:")
    for field in task.get("custom_fields", []):
        field_id = field.get("id")
        field_name = field.get("name")
        field_value = field.get("value")
        print(f"  - Field ID: {field_id}, Name: {field_name}, Value: {field_value}")
    print("-" * 40)

def main():
    # You can hard-code the list_id here or input it manually
    list_id = input("Enter the ClickUp list ID: ").strip()
    
    # Retrieve the API key from an environment variable or credentials file
    access_token = os.getenv('CLICKUP_API_KEY')
    if not access_token:
        try:
            with open('credentials.json') as f:
                access_token = json.load(f).get('CLICKUP_API_KEY')
        except Exception as e:
            print("Error loading API key:", e)
            return

    tasks = get_tasks(list_id, access_token)
    if not tasks:
        print("No tasks found or error retrieving tasks.")
        return
    
    # Print details for each task
    for task in tasks:
        print_task_details(task)

if __name__ == '__main__':
    main()
