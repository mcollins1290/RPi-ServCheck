#!/usr/bin/env python3.7

import configparser

EXITCODES = []

keytofind = 1

if __name__ == '__main__':

	exitcodes_filename = './exitcodes.txt'

	exitcodes = configparser.ConfigParser()
	exitcodes.read(exitcodes_filename)

	exitcodes_dict = {sect: dict(exitcodes.items(sect)) for sect in exitcodes.sections()}

	for key, value in exitcodes_dict.items():
		print(key, value)

	print ("Key to find: ", keytofind)
	print ("Value : ", exitcodes_dict.get('ExitCodes', {}).get(str(keytofind), 'Not Found'))
