import os
import json
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta, timezone
from dateutil.relativedelta import relativedelta

# ------------------------------
# CONFIGURATION / CONSTANTS
# ------------------------------
LIST_ID = "42370637"
DESTINATION_LIST_ID = "901201953178"
STATUS_ID = "sc42370637_Zea9lI9k"

BILLING_DAY_FIELD_ID = "dcd50ff8-4bed-4df2-a59b-3ce491837ae3"
PAYMENT_TERMS_FIELD_ID = "ab4efbc2-6835-49f8-a492-daf6f0eada34"
MOTHER_BRAND_FIELD_ID = "65152352-2245-4e01-a375-06f7094abc53"
RELATIONSHIP_FIELD_ID = "29aafb0f-2e62-4425-b409-5f21538b3c3c"

WATCHER_USER_ID = "81800000"  # Nadia

# ------------------------------
# API HELPER FUNCTIONS
# ------------------------------

def get_clickup_api_key():
    access_token = os.getenv('CLICKUP_API_KEY')
    if not access_token:
        try:
            with open('credentials.json') as f:
                access_token = json.load(f).get('CLICKUP_API_KEY')
        except Exception as e:
            print("Error loading API key:", e)
            exit(1)
    return access_token

def get_all_brand_tasks(list_id, status_id, access_token):
    tasks = []
    page = 0
    while True:
        url = f"https://api.clickup.com/api/v2/list/{list_id}/task?include_custom_fields=true&page={page}&limit=100"
        headers = {'Authorization': access_token, 'Content-Type': 'application/json'}
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

def group_tasks(tasks, mother_brand_field_id):
    active_ids = {task['id'] for task in tasks}
    dependent_tasks = []
    tentative_independent_tasks = []
    parent_ids = set()
    parent_children_names = {}  # parent_id -> list of child names
    parent_children_ids = {}    # parent_id -> list of child IDs

    for task in tasks:
        mother_id = None
        for field in task.get('custom_fields', []):
            if field['id'] == mother_brand_field_id and field.get('value'):
                mother_id = field['value'][0]['id']
                break
        if mother_id and mother_id in active_ids:
            dependent_tasks.append(task)
            parent_ids.add(mother_id)
            parent_children_names.setdefault(mother_id, []).append(task['name'])
            parent_children_ids.setdefault(mother_id, []).append(task['id'])
        else:
            tentative_independent_tasks.append(task)
    
    parent_tasks = []
    independent_tasks = []
    for task in tentative_independent_tasks:
        if task['id'] in parent_ids:
            parent_tasks.append(task)
        else:
            independent_tasks.append(task)
    
    return independent_tasks, dependent_tasks, parent_tasks, parent_children_names, parent_children_ids

def create_task(title, list_id, access_token, due_date):
    url = f"https://api.clickup.com/api/v2/list/{list_id}/task"
    headers = {'Authorization': access_token, 'Content-Type': 'application/json'}
    moscow_time = timezone(timedelta(hours=3))
    due_date = datetime.now(moscow_time)
    due_timestamp = int(due_date.timestamp() * 1000)
    
    data = {
        "name": title,
        "description": "Automatically created invoice task for billing period.",
        "due_date": due_timestamp
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code in [200, 201]:
        new_task_id = response.json().get('id')
        print(f"Task created: '{title}', ID: {new_task_id}")
        return new_task_id
    else:
        print(f"Failed to create task: {response.status_code} {response.text}")
        return None

def set_relationship_field(task_id, field_id, access_token, add_ids=None, remove_ids=None):
    url = f"https://api.clickup.com/api/v2/task/{task_id}/field/{field_id}"
    headers = {"Content-Type": "application/json", "Authorization": access_token}
    value_payload = {}
    if add_ids:
        value_payload['add'] = add_ids
    if remove_ids:
        value_payload['rem'] = remove_ids
    payload = {"value": value_payload}
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code in [200, 201]:
        print("Task relationship updated successfully.")
    else:
        print(f"Failed to update task relationship: {response.status_code} {response.text}")

def add_watcher(task_id, user_id, access_token):
    url = f"https://api.clickup.com/api/v2/task/{task_id}"
    headers = {"Authorization": access_token, "accept": "application/json", "content-type": "application/json"}
    payload = {"watchers": {"add": [user_id]}}
    response = requests.put(url, headers=headers, json=payload)
    if response.status_code in [200, 201]:
        print(f"Watcher {user_id} added to task {task_id}.")
    else:
        print(f"Failed to add watcher {user_id} to task {task_id}: {response.status_code} {response.text}")

def remove_watcher(task_id, user_id, access_token):
    url = f"https://api.clickup.com/api/v2/task/{task_id}"
    headers = {"Authorization": access_token, "accept": "application/json", "content-type": "application/json"}
    payload = {"watchers": {"rem": [user_id]}}
    response = requests.put(url, headers=headers, json=payload)
    if response.status_code in [200, 201]:
        print(f"Watcher {user_id} removed from task {task_id}.")
    else:
        print(f"Failed to remove watcher {user_id} from task {task_id}: {response.status_code} {response.text}")

def compute_invoice_task_details(billing_day, payment_term, brand_name, dependent_names, target_date):
    billing_day = int(billing_day)
    
    if billing_day == 1:
        if payment_term == 0:  # Pre-paid
            period_str = target_date.strftime("%m.%y")
        elif payment_term == 1:  # Post-paid
            prev_date = target_date - relativedelta(months=1)
            period_str = prev_date.strftime("%m.%y")
        title = f"{period_str} {brand_name}"
    else:
        try:
            if payment_term == 0:  # Pre-paid
                start_date = target_date.replace(day=billing_day)
                end_date = start_date + relativedelta(months=1) - timedelta(days=1)
            elif payment_term == 1:  # Post-paid (NEW logic)
                start_date = (target_date - relativedelta(months=1)).replace(day=billing_day)
                end_date = target_date.replace(day=billing_day) - timedelta(days=1)
            title = f"{start_date.strftime('%d.%m.%y')} - {end_date.strftime('%d.%m.%y')} {brand_name}"
        except ValueError as e:
            print(f"Invalid billing day {billing_day} for target month: {e}")
            return None

    if dependent_names:
        deps = " + ".join(dependent_names)
        title = f"{title} + {deps}"
    return title

# ------------------------------
# SMTP SETTINGS & EMAIL REPORTING FUNCTIONS
# ------------------------------

def get_smtp_settings():
    """
    Retrieve SMTP settings from environment variables.
    If not available, fallback to reading from credentials.json.
    """
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = os.getenv("SMTP_PORT")
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    if not (smtp_server and smtp_port and smtp_user and smtp_password):
        try:
            with open("credentials.json") as f:
                creds = json.load(f)
                smtp_server = smtp_server or creds.get("SMTP_SERVER")
                smtp_port = smtp_port or creds.get("SMTP_PORT")
                smtp_user = smtp_user or creds.get("SMTP_USER")
                smtp_password = smtp_password or creds.get("SMTP_PASSWORD")
        except Exception as e:
            print("Error loading SMTP settings:", e)
            exit(1)
    return smtp_server, int(smtp_port), smtp_user, smtp_password

def send_missing_fields_report(report_body):
    """
    Send an email with the report to sales@prpillar.com.
    SMTP settings are loaded via environment variables or credentials.json.
    """
    smtp_server, smtp_port, smtp_user, smtp_password = get_smtp_settings()
    sender_email = smtp_user
    recipient_email = "sales@prpillar.com"
    subject = "Missing Billing Fields Report"
    
    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = recipient_email
    msg["Subject"] = subject
    msg.attach(MIMEText(report_body, "plain"))
    
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.sendmail(sender_email, recipient_email, msg.as_string())
        server.quit()
        print("Report email sent successfully.")
    except Exception as e:
        print("Failed to send email:", e)

def generate_missing_fields_report(tasks):
    """
    Scan all tasks for missing billing day or payment term.
    Returns a report string if any task is missing required fields.
    """
    missing_entries = []
    for task in tasks:
        missing_fields = []
        billing_day_found = False
        payment_term_found = False
        for field in task.get("custom_fields", []):
            if field.get("id") == BILLING_DAY_FIELD_ID and field.get("value"):
                billing_day_found = True
            if field.get("id") == PAYMENT_TERMS_FIELD_ID and field.get("value") is not None:
                payment_term_found = True
        if not billing_day_found:
            missing_fields.append("Billing Day")
        if not payment_term_found:
            missing_fields.append("Payment Terms")
        if missing_fields:
            missing_entries.append(f"Brand '{task.get('name')}' (ID: {task.get('id')}) is missing: {', '.join(missing_fields)}")
    if missing_entries:
        report = "The following brands are missing required fields:\n\n" + "\n".join(missing_entries)
        return report
    else:
        return None

# ------------------------------
# MAIN EXECUTION
# ------------------------------

def main():
    access_token = get_clickup_api_key()
    tasks = get_all_brand_tasks(LIST_ID, STATUS_ID, access_token)
    print(f"Retrieved {len(tasks)} tasks from source list.")

    # Generate email report if any tasks are missing required fields.
    report = generate_missing_fields_report(tasks)
    if report:
        send_missing_fields_report(report)
    
    independent, dependent, parent, parent_children_names, parent_children_ids = group_tasks(tasks, MOTHER_BRAND_FIELD_ID)
    today = datetime.now(timezone.utc).date()
    target_date = today + timedelta(days=10)
    
    # Process Independent brands
    for task in independent:
        billing_day = None
        payment_term = None
        for field in task.get("custom_fields", []):
            if field.get("id") == BILLING_DAY_FIELD_ID and field.get("value"):
                billing_day = int(field.get("value"))
            if field.get("id") == PAYMENT_TERMS_FIELD_ID and field.get("value") is not None:
                payment_term = int(field.get("value"))
        if billing_day is None or payment_term is None:
            print(f"Skipping task '{task['name']}' due to missing billing day or payment terms.")
            continue
        
        if billing_day == target_date.day:
            title = compute_invoice_task_details(billing_day, payment_term, task['name'], [], target_date)
            if title:
                new_task_id = create_task(title, DESTINATION_LIST_ID, access_token, today)
                if new_task_id:
                    set_relationship_field(new_task_id, RELATIONSHIP_FIELD_ID, access_token, add_ids=[task['id']])
                    add_watcher(new_task_id, WATCHER_USER_ID, access_token)
                    remove_watcher(new_task_id, "6830798", access_token)
    
    # Process Parent brands
    for task in parent:
        billing_day = None
        payment_term = None
        for field in task.get("custom_fields", []):
            if field.get("id") == BILLING_DAY_FIELD_ID and field.get("value"):
                billing_day = int(field.get("value"))
            if field.get("id") == PAYMENT_TERMS_FIELD_ID and field.get("value") is not None:
                payment_term = int(field.get("value"))
        if billing_day is None or payment_term is None:
            print(f"Skipping parent task '{task['name']}' due to missing billing day or payment terms.")
            continue
        
        if billing_day == target_date.day:
            dependent_names = parent_children_names.get(task['id'], [])
            dependent_ids = parent_children_ids.get(task['id'], [])
            title = compute_invoice_task_details(billing_day, payment_term, task['name'], dependent_names, target_date)
            if title:
                new_task_id = create_task(title, DESTINATION_LIST_ID, access_token, today)
                if new_task_id:
                    related_ids = [task['id']] + dependent_ids
                    set_relationship_field(new_task_id, RELATIONSHIP_FIELD_ID, access_token, add_ids=related_ids)
                    add_watcher(new_task_id, WATCHER_USER_ID, access_token)
                    remove_watcher(new_task_id, "6830798", access_token)

if __name__ == '__main__':
    main()
