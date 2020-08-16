#!/usr/bin/env python3.7

try:
	import sys
	import os
	import subprocess
	import configparser
	import socket
	import smtplib

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

debug = False
sendEmail = False
rebootFilePath = './reboot'

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
	global debug
	usageMsg = "usage: " + sys.argv[0] + " <SendEmailwhenOK? (T/F)> <Optional: Debug? (T/F)>"

	if (len(argv) == 0 or len(argv) > 2):
		print(usageMsg)
		sys.exit(2)

	if (argv[0] != 'T' and argv[0] != 'F'):
		print(usageMsg)
		sys.exit(2)
	else:
		sendEmail = str2bool(argv[0])

	if len(argv) == 2:
		if (argv[1] != 'T' and argv[1] != 'F'):
			print(usageMsg)
			sys.exit(2)
		else:
			debug = str2bool(argv[1])

	if (debug):
		print ("DEBUG INFO: Send Email flag is set to: " + str(sendEmail))

def SendEmail(iFromEmail, iToEmail, iPassword, iSMTPHost, iSMTPPort, iEmailSubject, iEmailBody):
	global debug

	if (debug):
		print ("DEBUG INFO: Entering Send Email procedure")
		print ("DEBUG INFO: From Email: " + iFromEmail)
		print ("DEBUG INFO: To Email: " + iToEmail)
		print ("DEBUG INFO: Password: " + iPassword)
		print ("DEBUG INFO: SMTP Host: " + iSMTPHost)
		print ("DEBUG INFO: SMTP Port: " + str(iSMTPPort))
		print ("DEBUG INFO: Email Subject: [" + iEmailSubject + "]")
		print ("DEBUG INFO: Email Body: [" + iEmailBody + "]")

	# Set up the SMTP server connection
	try:
		s = smtplib.SMTP(iSMTPHost,iSMTPPort)
		s.starttls()
		s.login(iFromEmail, iPassword)
	except:
		print("ERROR: Unexpected error during SMTP Connection:", sys.exc_info())
		raise

	# Create a MIMEMultipart message required for email
	msg = MIMEMultipart()

	# Setup message parameters
	msg['From']=iFromEmail
	msg['To']=iToEmail
	msg['Subject']=iEmailSubject
	msg.attach(MIMEText(iEmailBody, 'plain'))

	# Now try and send Email
	try:
		s.send_message(msg)
		# Delete the message object now that the message has been sent
		del msg
		# Terminate the SMTP session and close the connection
		s.quit()
	except:
		print("ERROR: Unexpected error during email transmission:", sys.exc_info())
		raise

	if (debug):
		print ("DEBUG INFO: Leaving Send Email procedure")
	# Email sent successfully. Return success value
	return True

def getSettings():
	global GENERAL
	global SERVICES
	global EXITCODES
	global EMAILSETTINGS
	global debug
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
			for option in [ 'Enabled','OKExitCode','OKStatus','NotOKStatus' ]:
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
			'OKEXITCODE':config.getint('General','OKExitCode'),
			'OKSTATUS':config.get('General','OKStatus'),
			'NOTOKSTATUS':config.get('General','NotOKStatus')}
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
	global rebootFilePath
	global debug

	noOfOKServices = 0
	noOfNotOKServices = 0
	serviceStatusStr = ''
	failedServicesStr = ''
	emailBodyStr = ''
	emailSubjectStr = ''
	emailSubjectStatusStr = GENERAL['OKSTATUS']

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

	# Check if there are any enabled service(s) that are not OK
	if noOfNotOKServices > 0:
		# As there is at least one enabled Service that is not OK make sure email is sent
		if sendEmail == False:
			if (debug):
				print ("DEBUG INFO: At least one Service is in a 'Not OK' state. Set Send Email Flag to True")
			sendEmail = True
		# Update Email Subject Status to indicate a 'Not OK' status
		emailSubjectStatusStr = GENERAL['NOTOKSTATUS']

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
		# As there is at least one Service that is in a failed state make sure email is sent
		if sendEmail == False:
			if (debug):
				print ("DEBUG INFO: At least one Service is in a failed state. Set Send Email Flag to True")
			sendEmail = True
		if emailSubjectStatusStr == GENERAL['OKSTATUS']:
			# Update Email Subject Status to indicate a 'Not OK' status
			emailSubjectStatusStr = GENERAL['NOTOKSTATUS']
	else:
		failedServicesStr = 'No systemd units are in a failed state.'

	if sendEmail == False:
		# Exit Main function if no need to send email
		print ("INFO: All Services OK. No request to send email.")
		return

	if (debug):
		print ("DEBUG INFO: Now preparing email body & subject")

	# Prepare the Email Body string
	emailBodyStr = serviceStatusStr + '\n' + failedServicesStr + "\n\nIP Address: " + get_ip_address()
	if (debug):
		print ("DEBUG INFO: Email Body =\n[" + emailBodyStr + "]")

	# Prepare the Email Subject string
	emailSubjectStr = emailSubjectStatusStr + " - RPi Services Check Results for host " + socket.gethostbyaddr(socket.gethostname())[0]
	if (os.path.isfile(rebootFilePath)):
		emailSubjectStr = emailSubjectStr + " [REBOOT]"
		os.remove(rebootFilePath)

	if (debug):
		print ("DEBUG INFO: Email Subject =\n[" + emailSubjectStr + "]")

	# Attempt to send email
	retVal = SendEmail( 	EMAILSETTINGS['FROM_EMAIL'],
				EMAILSETTINGS['TO_EMAIL'],
				EMAILSETTINGS['PASSWORD'],
				EMAILSETTINGS['SMTP_HOST'],
				EMAILSETTINGS['SMTP_PORT'],
				emailSubjectStr,
				emailBodyStr)

	if (retVal):
		print ("INFO: Email sent successfully.")
	else:
		print ("ERROR: Email was not sent successfully.")
		sys.exit(1)

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
