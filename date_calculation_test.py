from datetime import datetime, timedelta

def calculate_dates(day_of_month):
    today = datetime.now()
    current_year = today.year
    current_month = today.month
    next_month = current_month + 1 if current_month < 12 else 1
    next_month_year = current_year if current_month < 12 else current_year + 1
    
    # Determine the start of the next billing period
    if today.day < day_of_month:
        start_date = datetime(current_year, current_month, day_of_month)
    else:
        start_date = datetime(next_month_year, next_month, day_of_month)
    
    # Calculate the end date of the billing period
    if start_date.month == 12:
        end_date = datetime(start_date.year + 1, 1, day_of_month) - timedelta(days=1)
    else:
        end_date = datetime(start_date.year, start_date.month + 1, day_of_month) - timedelta(days=1)

    # Determine the task creation date
    task_creation_date = start_date - timedelta(days=7)
    
    return task_creation_date, start_date, end_date

# Example usage:
day_of_month = 15  # Example value from your custom field
task_creation_date, start_date, end_date = calculate_dates(day_of_month)
print("Task Creation Date:", task_creation_date.strftime('%Y-%m-%d'))
print("Billing Period: From", start_date.strftime('%Y-%m-%d'), "to", end_date.strftime('%Y-%m-%d'))
