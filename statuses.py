import requests

def get_list_statuses(list_id, access_token):
    url = f"https://api.clickup.com/api/v2/list/{list_id}"
    headers = {
        'Authorization': access_token,
        'Content-Type': 'application/json'
    }
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        list_details = response.json()
        statuses = list_details.get('statuses', [])
        return statuses
    else:
        print(f"Failed to retrieve list statuses: {response.status_code}")
        return None

# Replace 'YOUR_ACCESS_TOKEN' with your actual ClickUp API token
access_token = 'pk_50289732_V33LDONURP1N1Y2O1Q5UN6QT19Z1F4W6'
list_id = "42370637"

# Retrieve statuses for the list
statuses = get_list_statuses(list_id, access_token)
if statuses:
    print("List statuses:")
    for status in statuses:
        print(f"Status ID: {status['id']}, Name: {status['status']}")
else:
    print("No statuses found or an error occurred.")
