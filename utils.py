# -*- coding: utf-8; indent-tabs-mode: t; tab-width: 4 -*-
#
# utils.py
#

class Utils:
	def perror(text):
		import sys
		sys.stderr.write('ERROR: '+text+'\n')

