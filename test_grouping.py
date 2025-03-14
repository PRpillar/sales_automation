import os
import json
import requests

def get_all_brand_tasks(list_id, status_id, access_token):
    """
    Retrieve all tasks from the specified ClickUp list using pagination,
    and filter them by the target status.
    """
    tasks = []
    page = 0
    while True:
        url = f"https://api.clickup.com/api/v2/list/{list_id}/task?include_custom_fields=true&page={page}&limit=100"
        headers = {
            'Authorization': access_token,
            'Content-Type': 'application/json'
        }
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"Failed to retrieve tasks on page {page}: {response.status_code}")
            break

        data = response.json()
        page_tasks = data.get('tasks', [])
        if not page_tasks:
            break

        tasks.extend(page_tasks)
        page += 1

    tasks = [task for task in tasks if task.get('status', {}).get('id') == status_id]
    return tasks

def group_tasks(tasks, parent_relationship_field_id):
    """
    Group tasks into three categories:
      - Dependent brands: tasks that have a mother brand specified in the custom field AND that mother brand is active.
      - Parent brands: active tasks that are referenced as a mother brand by at least one dependent brand.
      - Independent brands: tasks that either have no mother brand specified, or the specified mother brand is not active.
      
    Also builds a mapping of parent_id -> list of child brand names.
    """
    active_ids = {task['id'] for task in tasks}
    
    dependent_tasks = []
    tentative_independent_tasks = []
    parent_ids = set()
    # Mapping: parent_id -> list of child brand names
    parent_children = {}
    
    for task in tasks:
        mother_id = None
        for field in task.get('custom_fields', []):
            if field['id'] == parent_relationship_field_id and field.get('value'):
                # Assume the field's value is a list of dictionaries; we take the first one.
                mother_id = field['value'][0]['id']
                break

        # Classify as dependent only if the mother brand is active.
        if mother_id and mother_id in active_ids:
            dependent_tasks.append(task)
            parent_ids.add(mother_id)
            parent_children.setdefault(mother_id, []).append(task['name'])
        else:
            tentative_independent_tasks.append(task)
    
    parent_tasks = []
    independent_tasks = []
    for task in tentative_independent_tasks:
        if task['id'] in parent_ids:
            parent_tasks.append(task)
        else:
            independent_tasks.append(task)
    
    return independent_tasks, dependent_tasks, parent_tasks, parent_children

def main():
    # List IDs for ClickUp
    list_id = "42370637"
    destination_list_id = "901201953178"  # Not used in this step
    
    # The status ID to filter tasks on (Active status)
    status_id = "sc42370637_Zea9lI9k"
    
    # Custom field ID for the mother brand relationship
    parent_relationship_field_id = "65152352-2245-4e01-a375-06f7094abc53"
    
    # Retrieve the ClickUp API key
    access_token = os.getenv('CLICKUP_API_KEY') or json.load(open('credentials.json'))['CLICKUP_API_KEY']
    
    # Retrieve all tasks using pagination
    tasks = get_all_brand_tasks(list_id, status_id, access_token)
    print(f"Retrieved {len(tasks)} tasks.")
    
    # Group tasks into Independent, Dependent, and Parent brands and get the mapping of child brands.
    independent, dependent, parent, parent_children = group_tasks(tasks, parent_relationship_field_id)
    
    print("\nIndependent Brands:")
    for task in independent:
        print(f" - {task['name']}")
        
    print("\nDependent Brands:")
    for task in dependent:
        print(f" - {task['name']}")
    
    print("\nParent Brands:")
    for task in parent:
        # Retrieve the list of child brand names for this parent brand.
        children = parent_children.get(task['id'], [])
        children_str = ", ".join(children) if children else "No child brands"
        print(f" - {task['name']} ({children_str})")

if __name__ == '__main__':
    main()
