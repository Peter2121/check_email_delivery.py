#!/usr/bin/env python

import sys
import argparse
import ConfigParser
import imaplib
import re
import dateutil.parser
from datetime import datetime
import pytz
import inspect
import os
import time
import subprocess

EXIT_OK = 0
EXIT_WARNING = 1
EXIT_CRITICAL = 2
EXIT_UNKNOWN = 3

DEFAULT_PROFILECONFIG = '/etc/nagios-plugins/check_email_delivery_credentials.ini'
SCRIPT_SEND = 'check_smtp_send.py'
SCRIPT_RECEIVE = 'check_imap_receive.py'
SLEEP_SEC = 5

parser = argparse.ArgumentParser(description='This program test email delivery using SMTP and IMAP')
parser.add_argument('-H', dest='host', metavar='host', required=True, help='SMTP/IMAP host')
parser.add_argument('--profilesend', metavar='profilesend', required=True, help='credential profile for sending mail in config file')
parser.add_argument('--profilereceive', metavar='profilereceive', required=True, help='credential profile for receiving mail in config file')
parser.add_argument('--profileconfig', metavar='profileconfig', default=DEFAULT_PROFILECONFIG, help='location of the config file (default=%s)'%DEFAULT_PROFILECONFIG)
parser.add_argument('--body', metavar='body', help='Message body')
parser.add_argument('--subject', metavar='subject', help='Message subject')
parser.add_argument('--portsmtp', metavar='portsmtp', type=int, help='SMTP port')
parser.add_argument('--portimap', metavar='portimap', type=int, help='IMAP port')

try:
    args = vars(parser.parse_args())
except SystemExit:
    sys.exit(EXIT_UNKNOWN)

cur_file_name = inspect.getfile(inspect.currentframe())
cur_path = os.path.dirname(cur_file_name)

command_line_send = os.path.join(cur_path, SCRIPT_SEND)
command_line_receive = os.path.join(cur_path, SCRIPT_RECEIVE)

host = args['host']
profile_send = args['profilesend']
profile_receive = args['profilereceive']
profileconfig = args['profileconfig']

command_line_send = command_line_send + ' -H ' + host + ' --profile ' + profile_send + ' --profileconfig ' + profileconfig
command_line_receive = command_line_receive + ' -H ' + host + ' --profile ' + profile_receive + ' --profileconfig ' + profileconfig

if args['portsmtp'] is not None:
    port = args['portsmtp']
    command_line_send = command_line_send + ' --port ' + str(port)
if args['portimap'] is not None:
    port = args['portimap']
    command_line_receive = command_line_receive + ' --port ' + str(port)
if args['body'] is not None:
    body = args['body']
    command_line_send = command_line_send + ' --body ' + body
if args['subject'] is not None:    
    subject = args['subject']
    command_line_send = command_line_send + ' --subject ' + subject
    command_line_receive = command_line_receive + ' --subject ' + subject
#print('Send command line:\n%s' % command_line_send)
#print('Receive command line:\n%s' % command_line_receive)
#ret_code_send = os.system(command_line_send)
ret_code_send = subprocess.call(command_line_send, shell=True)
if ret_code_send == EXIT_CRITICAL:
    print('CRITICAL')
    sys.exit(EXIT_CRITICAL)
#print('Send: %d' % ret_code_send)
time.sleep(SLEEP_SEC)
#ret_code_receive = os.system(command_line_receive)
ret_code_receive = subprocess.call(command_line_receive, shell=True)
#print('Receive: %d' % ret_code_receive)
if ret_code_receive == EXIT_CRITICAL:
    print('CRITICAL')
    sys.exit(EXIT_CRITICAL)
if ret_code_receive == EXIT_WARNING:
    print('WARNING')
    sys.exit(EXIT_WARNING)
if ret_code_receive == EXIT_OK:
    if ret_code_send == EXIT_WARNING:
        print('WARNING')
        sys.exit(EXIT_WARNING)
    else:
        if ret_code_send == EXIT_OK:
            print('OK')
            sys.exit(EXIT_OK)
print('UNKNOWN')
sys.exit(EXIT_UNKNOWN)

