import os
import json
import requests

def get_all_users(access_token):
    """
    Retrieve all teams and their members from ClickUp, and return a dictionary
    mapping user IDs to a display name (username or email).
    """
    url = "https://api.clickup.com/api/v2/team"
    headers = {"Authorization": access_token}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Failed to retrieve teams: {response.status_code} {response.text}")
        return {}
    
    teams = response.json().get("teams", [])
    users = {}
    for team in teams:
        for member in team.get("members", []):
            user = member.get("user", {})
            user_id = user.get("id")
            user_name = user.get("username") or user.get("email") or "Unknown"
            users[user_id] = user_name
    return users

def main():
    # Retrieve the ClickUp API key from environment variable or credentials.json
    access_token = os.getenv("CLICKUP_API_KEY")
    if not access_token:
        try:
            with open("credentials.json") as f:
                access_token = json.load(f).get("CLICKUP_API_KEY")
        except Exception as e:
            print("Error loading API key:", e)
            return

    users = get_all_users(access_token)
    if not users:
        print("No users found.")
        return

    print("Users in your workspace:")
    for user_id, user_name in users.items():
        print(f"User ID: {user_id}, Name: {user_name}")

if __name__ == "__main__":
    main()
