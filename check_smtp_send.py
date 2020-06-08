##!/usr/bin/env python3

import sys
import argparse
import configparser
import smtplib
import datetime
import time
import uuid
from email.mime.text import MIMEText
from email import utils

EXIT_OK = 0
EXIT_WARNING = 1
EXIT_CRITICAL = 2
EXIT_UNKNOWN = 3

DEFAULT_PORT = 587
DEFAULT_PROFILECONFIG = '/etc/nagios-plugins/check_email_delivery_credentials.ini'
DEFAULT_BODY = 'This is a test message by the monitoring system to check if email delivery is running fine.'
DEFAULT_SUBJECT = 'TEST'
DEFAULT_MAILFROM = ''
DEFAULT_MAILTO = ''

parser = argparse.ArgumentParser(description='This program sends a test email message over SMTP TLS.')
parser.add_argument('-H', dest='host', metavar='host', required=True, help='SMTP host')
parser.add_argument('--port', type=int, default=DEFAULT_PORT, help='SMTP port (default=%i)'%DEFAULT_PORT)
parser.add_argument('--profile', required=True, help='credential profile in config file')
parser.add_argument('--profileconfig', metavar='config.ini', default=DEFAULT_PROFILECONFIG, help='location of the config file (default=%s)'%DEFAULT_PROFILECONFIG)
parser.add_argument('--mailfrom', metavar='sender@host1', default=DEFAULT_MAILFROM, help='email address of the test message sender')
parser.add_argument('--mailto', metavar='receiver@host2', default=DEFAULT_MAILTO, help='email address of the test message receiver')
parser.add_argument('--body', metavar='body', default=DEFAULT_BODY, help='Message body')
parser.add_argument('--subject', metavar='subject', default=DEFAULT_SUBJECT, help='Message subject')


try:
    args = vars(parser.parse_args())
except SystemExit:
    sys.exit(EXIT_UNKNOWN)

host = args['host']
port = args['port']
profile = args['profile']
profileconfig = args['profileconfig']
mailfrom = args['mailfrom']
mailto = args['mailto']
body = args['body']
subject = args['subject']

config = configparser.ConfigParser()
config.read(profileconfig)

try:
    username = config.get(profile,'username')
    password = config.get(profile,'password')
    if mailfrom == DEFAULT_MAILFROM:
        mailfrom = config.get(profile,'mailfrom')
    if mailto == DEFAULT_MAILTO:
        mailto = config.get(profile,'mailto')
except ConfigParser.NoSectionError:
    print('Configuration error: profile %s does not exist' % profile)
    sys.exit(EXIT_UNKNOWN)
except ConfigParser.NoOptionError:
    print('Configuration error: profile %s does not contain correct data' % profile)
    sys.exit(EXIT_UNKNOWN)

msg = MIMEText(body)
msg['Subject'] = subject
msg['From'] = mailfrom
msg['To'] = mailto
msg['Message-ID'] = '<' + str(uuid.uuid4()) + '@' + host + '>'
#msg.add_header('X-Nature', 'Test LibreNMS')

nowdt = datetime.datetime.now()
nowtuple = nowdt.timetuple()
nowtimestamp = time.mktime(nowtuple)

msg['Date'] = utils.formatdate(nowtimestamp)

try:
    smtp = smtplib.SMTP(host, port)
    smtp.starttls()
    if username != '':
        smtp.login(username, password)
    smtp.sendmail(mailfrom, mailto, msg.as_string())
except smtplib.SMTPServerDisconnected as e:
    # This exception is raised when the server unexpectedly disconnects, or when an attempt is made to use the SMTP instance before connecting it to a server.
    print ('SMTPServerDisconnected: ', e)
    sys.exit(EXIT_CRITICAL)
except smtplib.SMTPResponseException as e:
    # Base class for all exceptions that include an SMTP error code. These exceptions are generated in some instances when the SMTP server returns an error code. The error code is stored in the smtp_code attribute of the error, and the smtp_error attribute is set to the error message.
    print ('SMTPResponseException: ', e)
    sys.exit(EXIT_CRITICAL)
except smtplib.SMTPSenderRefused as e:
    # Sender address refused. In addition to the attributes set by on all SMTPResponseException exceptions, this sets 'sender' to the string that the SMTP server refused.
    print ('SMTPSenderRefused: ', e)
    sys.exit(EXIT_CRITICAL)
except smtplib.SMTPRecipientsRefused as e:
    # All recipient addresses refused. The errors for each recipient are accessible through the attribute recipients, which is a dictionary of exactly the same sort as SMTP.sendmail() returns.
    print ('SMTPRecipientsRefused: ', e)
    sys.exit(EXIT_CRITICAL)
except smtplib.SMTPDataError as e:
    # The SMTP server refused to accept the message data.
    print ('SMTPDataError: ', e)
    sys.exit(EXIT_CRITICAL)
except smtplib.SMTPConnectError as e:
    # Error occurred during establishment of a connection with the server.
    print ('SMTPConnectError: ', e)
    sys.exit(EXIT_CRITICAL)
except smtplib.SMTPHeloError as e:
    # The server refused our HELO message.
    print ('SMTPHeloError: ', e)
    sys.exit(EXIT_CRITICAL)
except smtplib.SMTPAuthenticationError as e:
    # SMTP authentication went wrong. Most probably the server didn't accept the username/password combination provided.
    print ('SMTPResponseException: ', e)
    sys.exit(EXIT_CRITICAL)
except smtplib.SMTPException as e:
    # The base exception class for all the other exceptions provided by this module.
    print ('SMTPException: ', e)
    sys.exit(EXIT_CRITICAL)

print('OK')
sys.exit(EXIT_OK)


