# Sales Automation

A collection of Python scripts for managing and automating sales operations with ClickUp.

## Overview

This project provides tools to automate various sales-related tasks using the ClickUp API, including:

- Automated invoice task creation based on billing periods
- Data backup from ClickUp (spaces, folders, lists, tasks, comments, docs)
- Team member information retrieval
- Custom field management

## Requirements

- Python 3.6+
- ClickUp API access
- Required Python packages (see requirements.txt)

## Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/sales_automation.git
cd sales_automation
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a credentials.json file with your ClickUp API key:
```json
{
  "CLICKUP_API_KEY": "your_clickup_api_key_here",
  "SMTP_SERVER": "smtp.example.com",
  "SMTP_PORT": "587",
  "SMTP_USER": "your_email@example.com",
  "SMTP_PASSWORD": "your_email_password"
}
```

## Core Scripts

### main.py
- Main billing automation script
- Creates invoice tasks based on billing days
- Groups related brands together
- Sends email reports for missing billing information

### backup.py
- Backs up data from ClickUp to CSV files
- Retrieves spaces, folders, lists, tasks, and comments
- Uses pagination to handle large data sets

### backup_docs.py
- Backs up ClickUp documents to CSV files
- Retrieves document content in Markdown format

### backup_comments.py
- Specifically backs up task comments
- Paginates through comments for comprehensive backup

### get_team_members.py
- Retrieves team member information from ClickUp

## Helper Scripts

### custom_field_ids.py
- Utilities for working with ClickUp custom fields

### statuses.py
- Functions related to ClickUp statuses

### relationships.py
- Handles relationships between different ClickUp items

### test_*.py files
- Test scripts for various functionality

## Usage

### Running the invoice automation:

```bash
python main.py
```

### Backing up ClickUp data:

```bash
python backup.py
```

### Backing up ClickUp docs:

```bash
python backup_docs.py
```

## Data Files

The scripts generate various CSV files:
- spaces.csv: ClickUp spaces information
- folders.csv: Folder information 
- lists.csv: List information
- tasks.csv: Task information
- comments.csv: Comment data
- docs.csv: Document data
- doc_pages.csv: Document page content

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request