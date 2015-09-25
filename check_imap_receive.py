#!/usr/bin/env python

import sys
import argparse
import ConfigParser
import imaplib
import re
import dateutil.parser
from datetime import datetime
import pytz

EXIT_OK = 0
EXIT_WARNING = 1
EXIT_CRITICAL = 2
EXIT_UNKNOWN = 3

DEFAULT_PORT = 993
DEFAULT_PROFILECONFIG = '/etc/nagios-plugins/check_email_delivery_credentials.ini'
DEFAULT_WARN = 120
DEFAULT_CRIT = 600

parser = argparse.ArgumentParser(description='This program checks if the most recent mail in an IMAP inbox is not older than a certain time. Use this check as a companion to check_smtp_send.py, which sends test email messages.')
parser.add_argument('-H', dest='host', metavar='host', required=True, help='SMTP host')
parser.add_argument('--port', type=int, default=DEFAULT_PORT, help='SMTP port (default=%i)'%DEFAULT_PORT)
parser.add_argument('--profile', required=True, help='credential profile in config file')
parser.add_argument('--profileconfig', metavar='config.ini', default=DEFAULT_PROFILECONFIG, help='location of the config file (default=%s)'%DEFAULT_PROFILECONFIG)
parser.add_argument('-w', metavar='warningseconds', dest='warn', default=DEFAULT_WARN, help='warn, if the most recent message is older than this value (default=%s)' % DEFAULT_WARN)
parser.add_argument('-c', metavar='criticalseconds', dest='crit', default=DEFAULT_CRIT, help='critical, if the most recent message is older than this value (default=%s)' % DEFAULT_CRIT)

try:
    args = vars(parser.parse_args())
except SystemExit:
    sys.exit(EXIT_UNKNOWN)

host = args['host']
port = args['port']
profile = args['profile']
profileconfig = args['profileconfig']
warn = args['warn']
crit = args['crit']

config = ConfigParser.SafeConfigParser()
config.read(profileconfig)

try:
    username = config.get(profile,'username')
    password = config.get(profile,'password')
except ConfigParser.NoSectionError:
    print('Configuration error: profile %s does not exist' % profile)
    sys.exit(EXIT_UNKNOWN)
except ConfigParser.NoOptionError:
    print('Configuration error: profile %s does not contain username or password' % profile)
    sys.exit(EXIT_UNKNOWN)

imap = imaplib.IMAP4_SSL(host, port)
imap.login(username, password)
imap.select()
typ, data = imap.search(None, 'ALL')

pattern = re.compile(r'\(INTERNALDATE "(.+)"\)')

messages = []
for num in data[0].split():
    typ, data = imap.fetch(num, '(INTERNALDATE)')
    if typ != 'OK':
        # TODO: error handling
        sys.exit(EXIT_UNKNOWN)
    m = pattern.search(data[0])
    d = dateutil.parser.parse(m.group(1))
    messages.append((d,num))

sortedmessages = sorted(messages, key=lambda x: x[0])

print sortedmessages

mostrecent = sortedmessages[-1]
for d,num in sortedmessages[:-1]:
    imap.store(num, '+FLAGS', '\\Deleted')

imap.expunge()
imap.close()
imap.logout()

sec = (datetime.now(pytz.utc) - mostrecent[0]).total_seconds()

def print_message(status):
    print "%s|mostrecent=%i;%i;%i;0;" % (status, sec, warn, crit)

if sec > crit:
    print_message('CRITICAL') 
    sys.exit(EXIT_CRITICAL)
elif sec > warn:
    print_message('WARNING')
    sys.exit(EXIT_WARNING)

print_message('OK')
sys.exit(EXIT_OK)
