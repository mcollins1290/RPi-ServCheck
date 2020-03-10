#!/usr/bin/env python3.7

try:
	import sys
	import os
	import configparser

	from email.mime.multipart import MIMEMultipart
	from email.mime.text import MIMEText

except ImportError as e:
	print("ERROR: Error loading module: " + str(e))
	sys.exit(1)

## GLOBAL DICTS ##
GENERAL = []
SERVICES = []
EXITCODES = []
EMAILSETTINGS = []

## GLOBAL VARS ##

debug = True
sendEmailonOK = True

#################

def str2bool(str):
	return str == "T"

def chkArgs(argv):
	global sendEmailonOK
	usageMsg = "usage: " + sys.argv[0] + " <SendEmailOnOK? (T/F)>"

	if len(argv) != 1:
		print(usageMsg)
		sys.exit(2)

	if argv[0] != 'T' and argv[0] != 'F':
		print(usageMsg)
		sys.exit(2)

	sendEmailonOK = str2bool(argv[0])

def getSettings():
	global GENERAL
	global SERVICES
	global EXITCODES
	global EMAILSETTINGS
	settings_filename = './settings.ini'

	config = configparser.ConfigParser()
	config.read(settings_filename)

	# If settings file is missing, print error to CLI and Exit
	if not config.sections():
		print("ERROR: "+ settings_filename + " is missing. Exiting...")
		sys.exit(1)

	# File exists, check sections and options are present. If not, print error to CLI and Exit.
	for section in [ 'General','Services','ExitCodes','EmailSettings' ]:
		if not config.has_section(section):
			print("ERROR: Missing config file section: " + section +". Please check " + settings_filename)
			sys.exit(1)

		if section == 'General':
			for option in [ 'Enabled' ]:
				if not config.has_option(section, option):
					print("ERROR: Missing " + section + " option: " + option +". Please check " + settings_filename)
					sys.exit(1)

		if section == 'EmailSettings':
			for option in [ 'FromEmail','ToEmail','Password','SMTPHost','SMTPPort' ]:
				if not config.has_option(section, option):
					print("ERROR: Missing " + section + " option: " + option +". Please check " + settings_filename)
					sys.exit(1)

	# Settings file sections and options valid. Now retrieve/parse values and store in global dicts
	try:
		# Populate General dict
		GENERAL = {'ENABLED':config.getboolean('General', 'Enabled')}
		# Populate Email Settings dict
		EMAILSETTINGS =	{
			'FROM_EMAIL':config.get('EmailSettings', 'FromEmail'),
			'TO_EMAIL':config.get('EmailSettings', 'ToEmail'),
			'PASSWORD':config.get('EmailSettings', 'Password'),
			'SMTP_HOST':config.get('EmailSettings', 'SMTPHost'),
			'SMTP_PORT':config.getint('EmailSettings', 'SMTPPort')}
		# Populate Exit Codes dict
		EXITCODES = {sect: dict(config.items(sect)) for sect in config.sections()}

		################## DEBUGGING ##################
		if (debug):
			for key, value in GENERAL.items():
				print(key, value)
			for key, value in EMAILSETTINGS.items():
                        	print(key, value)
			for key, value in EXITCODES.items():
                        	print(key, value)
		###############################################

	except ValueError as e:
		print("ERROR: Unable to parse values from settings file: \n" + str(e))
		sys.exit(1)

if __name__ == '__main__':

	# First check that script is being run as root user.
	if not os.geteuid() == 0:
		print("ERROR: This Python script must be run as root.")
		sys.exit(1)
	# Script is being run as root. Continue...
	# Debug Status
	if (debug):
		print("INFO: DEBUGGING ENABLED\n")
	chkArgs(sys.argv[1:])
	getSettings()
	sys.exit(0)
