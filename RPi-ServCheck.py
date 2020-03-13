#!/usr/bin/env python3.7

try:
	import sys
	import os
	import subprocess
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
			for option in [ 'Enabled','OKExitCode' ]:
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
		GENERAL = {
			'ENABLED':config.getboolean('General', 'Enabled'),
			'OKEXITCODE':config.getint('General','OKExitCode')}
		# Populate Email Settings dict
		EMAILSETTINGS =	{
			'FROM_EMAIL':config.get('EmailSettings', 'FromEmail'),
			'TO_EMAIL':config.get('EmailSettings', 'ToEmail'),
			'PASSWORD':config.get('EmailSettings', 'Password'),
			'SMTP_HOST':config.get('EmailSettings', 'SMTPHost'),
			'SMTP_PORT':config.getint('EmailSettings', 'SMTPPort')}
		# Populate Exit Codes dict
		EXITCODES = dict(config.items('ExitCodes'))
		# Populate Services dict
		SERVICES = dict(config.items('Services'))

		################## DEBUGGING ##################
		if (debug):
			print("DEBUG INFO: Dumping Dictionary Keys & Values:\n")
			for key, value in GENERAL.items():
				print(key, value)
			for key, value in EMAILSETTINGS.items():
				print(key, value)
			for key, value in EXITCODES.items():
				print(key, value)
			for key, value in SERVICES.items():
				print(key, value)
			print("\nDEBUG INFO: Dump Complete")
		###############################################

	except ValueError as e:
		print("ERROR: Unable to parse values from settings file: \n" + str(e))
		sys.exit(1)

def main():
	global GENERAL
	global SERVICES
	global EXITCODES
	global EMAILSETTINGS

	noOfOKServices = 0
	noOfNotOKServices = 0
	serviceStatusStr = ''
	failedServicesStr = ''

	# Check Enabled flag in settings file is set to True, otherwise print message and exit
	if not(GENERAL['ENABLED']):
		print("INFO: 'Enabled' flag in settings file is not set to True. Exiting...")
		sys.exit(0)

	# Iterate through Services dict, check Service status for each enabled Service
	for serviceName,toCheck in SERVICES.items():
		# Only check enabled services
		if toCheck.lower() == 'true':
			# Build OS Command to check Service status
			osCommand = 'systemctl status ' + serviceName + ' > /dev/null 2>&1'
			# Execute OS Command and extract Exit Code
			exitCode = os.WEXITSTATUS(os.system(osCommand))
			if (debug):
				print ('DEBUG INFO: ' + serviceName + ' exit code is: ' + str(exitCode) + ' : ' + EXITCODES.get(str(exitCode), 'Unknown Exit Code'))
			# Based on extracted Exit Code, increment OK and Not OK counts
			if exitCode == GENERAL['OKEXITCODE']:
				noOfOKServices += 1
			else:
				noOfNotOKServices += 1
			# Add to string keeping a record of services checked along with their Exit Code info.
			serviceStatusStr += serviceName + ': ' + str(exitCode) + ' (' + EXITCODES.get(str(exitCode), 'Unknown Exit Code') + ')\n'

	# Now check for any systemd units in failed status
	osCommand = 'systemctl list-units --state=failed --no-legend'
	proc = subprocess.Popen(osCommand, stdout=subprocess.PIPE, shell=True)
	osCommandOutput = proc.stdout.read().decode('UTF-8')

	i = 0
	if len(osCommandOutput) > 0:
		failedServicesStr = 'The following services are in a failed state:\n'
		for line in osCommandOutput.split('\n'):
			if len(line) > 0:
				if i > 0:
					failedServicesStr += '\n'
				failedServicesStr += line.split(' ')[0]
				i += 1
	else:
		failedServicesStr = 'No systemd units are in a failed state.'

	print("#" + failedServicesStr + "#")


if __name__ == '__main__':

	# First check that script is being run as root user.
	if not os.geteuid() == 0:
		print("ERROR: This Python script must be run as root.")
		sys.exit(1)
	# Script is being run as root. Continue...
	# Debug Status
	if (debug):
		print("DEBUG INFO: DEBUGGING ENABLED\n")
	chkArgs(sys.argv[1:])
	getSettings()
	main()
	# Program complete. Exit cleanly
	if (debug):
		print("DEBUG INFO: Process completed successfully. Exiting...")
	sys.exit(0)
