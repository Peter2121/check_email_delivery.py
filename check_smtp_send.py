import sys
import argparse
import ConfigParser
import smtplib
from email.mime.text import MIMEText
from email import utils
import datetime
import time
import uuid

parser = argparse.ArgumentParser(description='foo')
parser.add_argument('-H', required=True)
parser.add_argument('--port', type=int, default=587)
parser.add_argument('--profile', required=True)
parser.add_argument('--profileconfig', default='/etc/nagios-plugins/check_email_delivery_credentials.ini')
parser.add_argument('--mailfrom', required=True)
parser.add_argument('--mailto', required=True)
args = vars(parser.parse_args())

host = args['H']
port = args['port']
profile = args['profile']
profileconfig = args['profileconfig']
mailfrom = args['mailfrom']
mailto = args['mailto']

config = ConfigParser.SafeConfigParser()
config.read(profileconfig)

try:
    username = config.get(profile,'username')
    password = config.get(profile,'password')
except ConfigParser.NoSectionError:
    sys.exit('profile %s does not exist' % profile)
except ConfigParser.NoOptionError:
    sys.exit('profile %s does not contain username or password' % profile)

smtp = smtplib.SMTP(host, port)
smtp.starttls()
smtp.login(username, password)

#msg = ('From: %s\r\nTo: %s\r\n\r\n' % (mailfrom, mailto))
msg = MIMEText('This is a test message')
msg['Subject'] = 'TEST'
msg['From'] = mailfrom
msg['To'] = mailto
msg['Message-ID'] = '<' + str(uuid.uuid4()) + '@' + host + '>'

nowdt = datetime.datetime.now()
nowtuple = nowdt.timetuple()
nowtimestamp = time.mktime(nowtuple)

msg['Date'] = utils.formatdate(nowtimestamp)

smtp.sendmail(mailfrom, mailto, msg.as_string())


