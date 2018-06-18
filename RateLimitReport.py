"""
This script monitors a central limits collection generated by STACK and sends a daily notification.

This script was extended from Sam Jackson's ServerReport [https://github.com/sjacks26/ServerReport]
"""
import sys
import datetime
from email.message import EmailMessage
import os
import time
import smtplib
import numpy as np
import pymongo
import logging

import config as cfg

logging.basicConfig(filename=cfg.script_log_file,filemode='a+',level=logging.INFO)

def check_rate_limit():
    """
    This function checks the central rate limits collection, returning a list of rate limits aggregated by project, server and date.
    """
    try:
        mongoClient = pymongo.MongoClient(cfg.mongo_account['address'])
    
        if cfg.mongo_account['auth']:
            mongoClient.admin.authenticate(cfg.mongo_account['username'], cfg.mongo_account['password'])
    
        mongoDB = mongoClient[cfg.db_name][cfg.col_name]
    except:
        return False
    
    limits_agg = {}
    
    today = datetime.date.today()
    yesterday = today.replace(day=(today.day - 1)).isoformat()
    
    limits = mongoDB.find({'time': {'$gte': yesterday}})
    
    for limit in limits:
        server_name = limit['server_name']
        project_name = limit['project_name']
        limit_datetime = datetime.datetime.fromtimestamp(int(limit['timestamp_ms'])/1000).strftime('%Y-%m-%d')
        
        if server_name not in limits_agg:
            limits_agg[server_name] = {}
        if project_name not in limits_agg[server_name]:
            limits_agg[server_name][project_name] = 0
            
        limits_agg[server_name][project_name] += int(limit['lost_count'])
    
    return limits_agg

def send_daily_rate_limit_email(rate_limits, email_recipients=cfg.daily_status_email_recipients):
    """
    email_recipients should be a list.
    This assumes that the email will be sent using a gmail account
    """
    if not type(email_recipients) is list:
        raise Exception("Email recipients must be in a list")
    
    if len(rate_limits) > 0:
        status = 'Warning'
    else:
        status = 'OK'
        
    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days=1)

    email_text = 'A Summary of Rate Limits Report for ' + str(yesterday) + '\n '
    
    for server_name in rate_limits:
        email_text += '\n '
        email_text += 'Host: ' + server_name + '\n'
        
        for project_name in rate_limits[server_name]:
            email_text += '  - ' + project_name + ': Lost ' + str(rate_limits[server_name][project_name])

    email = EmailMessage()
    email.set_content(email_text)
    email['Subject'] = 'Rate Limits Summary: Status ' + status
    email['From'] = cfg.account_to_send_emails + '@gmail.com'
    email['To'] = ", ".join(email_recipients)

    server = smtplib.SMTP(cfg.email_server[0], cfg.email_server[1])
    server.starttls()
    server.login(cfg.account_to_send_emails, cfg.password_to_send_emails)
    server.sendmail(email['From'], email_recipients, email.as_string())
    server.quit()

    logging.info(today.isoformat() + ':  {0}: Status {1}'.format(cfg.server_name, status))

def script_error_email(error, email_recipients=cfg.warning_email_recipients):
    """
    This function immediately sends a warning email if the server watch code raises an exception.
    """
    if not type(email_recipients) is list:
        raise Exception("Email recipients must be in a list")
    email = EmailMessage()
    email_text = "Server watch script error: \n\n {}".format(error)
    email.set_content(email_text)
    email['Subject'] = "{0}: Critical - rate limit code error".format(cfg.server_name)
    email['From'] = cfg.account_to_send_emails + '@gmail.com'
    email['To'] = ", ".join(email_recipients)

    server = smtplib.SMTP(cfg.email_server[0], cfg.email_server[1])
    server.starttls()
    server.login(cfg.account_to_send_emails, cfg.password_to_send_emails)
    server.sendmail(email['From'], email_recipients, email.as_string())
    server.quit()

def run_rate_limits():
    try:
        rate_limits = check_rate_limit()
        send_daily_rate_limit_email(rate_limits=rate_limits)
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        logging.exception(e)
        script_error_email(e)
        
    logging.info("Daily report done. Sleeping until tomorrow.\n")
    

if __name__ == '__main__':
    while True:
        run_rate_limits()
        sleep = True
        while sleep:
            time.sleep(60*60)
            now = datetime.datetime.now()
            if now.hour == cfg.time_to_run:
                sleep = False