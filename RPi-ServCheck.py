#!/usr/bin/env python3.7

try:
	import sys
	import os
	import subprocess
	import configparser
	import socket

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
sendEmail = False

#################

def str2bool(str):
	return str == "T"

def get_ip_address():
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	s.connect(("8.8.8.8", 80)) #Google DNS IP for connection test
	ip_addr = s.getsockname()[0]
	s.close()
	return(ip_addr)

def chkArgs(argv):
	global sendEmail
	usageMsg = "usage: " + sys.argv[0] + " <SendEmailwhenOK? (T/F)>"

	if len(argv) != 1:
		print(usageMsg)
		sys.exit(2)

	if argv[0] != 'T' and argv[0] != 'F':
		print(usageMsg)
		sys.exit(2)

	sendEmail = str2bool(argv[0])

	if (debug):
		print ("DEBUG INFO: Send Email flag is set to: " + str(sendEmail))

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
			print("\nDEBUG INFO: Dictionary Dump Complete")
		###############################################

	except ValueError as e:
		print("ERROR: Unable to parse values from settings file: \n" + str(e))
		sys.exit(1)

def main():
	global GENERAL
	global SERVICES
	global EXITCODES
	global EMAILSETTINGS
	global sendEmail

	noOfOKServices = 0
	noOfNotOKServices = 0
	serviceStatusStr = ''
	failedServicesStr = ''
	emailBodyStr = ''
	emailSubjectStr = ''

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

	if (noOfOKServices == 0 and noOfNotOKServices == 0):
		# No services are enabled in settings.ini file
		serviceStatusStr = 'No services are enabled, please check settings file.\n'
	else:
		# Add counts to Service Status string
		serviceStatusStr = 'There is ' + str(noOfOKServices) + " Service(s) in 'OK' status and " + str(noOfNotOKServices) + " Service(s) that are in 'Not OK' status:\n" + serviceStatusStr
	# Build OS Command string to check for any failed systemd units
	osCommand = 'systemctl list-units --state=failed --no-legend'
	# Execute the OS Command
	proc = subprocess.Popen(osCommand, stdout=subprocess.PIPE, shell=True)
	# Read the stdout of the OS Command execution
	osCommandOutput = proc.stdout.read().decode('UTF-8')

	# Now check for any failed systemd units and prepare a string accordingly
	i = 0
	if len(osCommandOutput) > 0:
		for line in osCommandOutput.split('\n'):
			if len(line) > 0:
				if i > 0:
					failedServicesStr += '\n'
				failedServicesStr += line.split(' ')[0]
				i += 1
		if i > 1:
			failedServicesStr = 'The following ' + str(i) + ' services are in a failed state:\n' + failedServicesStr
		else:
			failedServicesStr = 'The following service is in a failed state:\n' + failedServicesStr
		# As there is at least one Service that is not OK make sure email is sent
		if sendEmail == False:
			if (debug):
				print ("DEBUG INFO: At least one Service is in a failed state. Set Send Email Flag to True")
			sendEmail = True
	else:
		failedServicesStr = 'No systemd units are in a failed state.'

	if sendEmail == False:
		# Exit Main function if no need to send email
		if (debug):
			print ("DEBUG INFO: All Services OK. No request to send email.")
		return

	if (debug):
		print ("DEBUG INFO: Now preparing email body & subject")

	# Prepare the Email Body string
	emailBodyStr = serviceStatusStr + '\n' + failedServicesStr + "\n\nIP Address: " + get_ip_address()
	if (debug):
		print ("DEBUG INFO: Email Body =\n[" + emailBodyStr + "]")

	# Prepare the Email Subject string
	emailSubjectStr = "RPi Services Check Results for host " + get_ip_address()
	if (debug):
		print ("DEBUG INFO: Email Subject =\n[" + emailSubjectStr + "]")

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
