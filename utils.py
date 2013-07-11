# -*- coding: utf-8; indent-tabs-mode: t; tab-width: 4 -*-
#
# utils.py
#


class Utils:

	
	# print error message.
	def perror(text):
		import sys
		sys.stderr.write('ERROR: '+text+'\n')


	# convert some data into corresponding integer value
	# or -1 if cannot.
	def safeInt(data):
		try:
			return int(data)
		except ValueError:
			return -1
	
	# convert some data into corresponding float value
	# or -1.0 if cannot.
	def safeFloat(data):
		try:
			return float(data)
		except ValueError:
			return -1.0
	
