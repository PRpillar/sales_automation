import requests
import os
import json

def get_custom_fields(list_id, access_token):
    url = f"https://api.clickup.com/api/v2/list/{list_id}/field"
    headers = {
        'Authorization': access_token,
        'Content-Type': 'application/json'
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        fields = response.json()
        return fields
    else:
        print(f"Failed to retrieve custom fields: {response.status_code}")
        return None

# Replace 'YOUR_ACCESS_TOKEN' with your actual ClickUp API token
access_token = os.getenv('CLICKUP_API_KEY') or json.load(open('credentials.json'))['CLICKUP_API_KEY']
list_id = "42370637"

# Retrieve custom fields
custom_fields = get_custom_fields(list_id, access_token)
if custom_fields:
    print("Custom Fields:")
    print(custom_fields)
else:
    print("No custom fields found or an error occurred.")
