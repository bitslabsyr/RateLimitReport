"""
This file contains parameters used by main.py
"""

server_name = 'SERVER_NAME'
time_to_run = 1

script_log_file = './script.log'

warning_email_recipients = ["SAMPLE@EMAIL"]
daily_status_email_recipients = ["SAMPLE@EMAIL", "SAMPLE@EMAIL"]
account_to_send_emails = 'USERNAME'         # must be a gmail account. Don't include "@gmail.com"
password_to_send_emails = 'PASSWORD'
email_server = ("smtp.gmail.com", 587)     # This should always work for gmail

stats_archive_dir = './log/'

# MongoDB info for rate limits checker
mongo_account = {
    "address": "MONGODB_SERVER",
    "auth": True,
    "username": "MONGODB_USERNAME",
    "password": "MONGODB_PASSWORD"
}

db_name = 'CENTRAL_LIMITS_DB_NAME'
col_name = 'CENTRAL_LIMITS_COL_NAME'