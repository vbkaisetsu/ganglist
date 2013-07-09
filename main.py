# -*- coding: utf-8; indent-tabs-mode: t; tab-width: 4 -*-
#
# main.py
#

from settings import Options


def perror(text):
	import sys
	sys.stderr.write('ERROR: '+text+'\n')


# parse options
def parseOptions():
	from optparse import OptionParser

	q = OptionParser()

	# add options into parser
	q.add_option('-W', '--width', dest='width',
		default=str(Options.DEFAULT_WIDTH),
		help='graph width (default: %d)' % Options.DEFAULT_WIDTH,
		metavar='<INT>')
	q.add_option('-H', '--height', dest='height',
		default=str(Options.DEFAULT_HEIGHT),
		help='graph height (default: %d)' % Options.DEFAULT_HEIGHT,
		metavar='<INT>')
	
	# analyze
	(options, args) = q.parse_args()

	# for debug
	#print(options)
	#print(args)

	return options, args


# assert options and convert data type if necessary
def checkOptions(options):

	def forceInteger(options, name):
		val = getattr(options, name)
		if not val.isdigit():
			raise ValueError('Option "%s" must be integer.' % name)
		setattr(options, name, int(val))

	def assertRange(options, name, minval, maxval):
		val = getattr(options, name)
		if val < minval or val > maxval:
			raise ValueError('Option "%s" must be: %d <= %s <= %d.' % (name, minval, name, maxval))
	
	try:
		forceInteger(options, 'width')
		forceInteger(options, 'height')
		assertRange(options, 'width', Options.MIN_WIDTH, Options.MAX_WIDTH)
		assertRange(options, 'height', Options.MIN_HEIGHT, Options.MAX_HEIGHT)
	except ValueError as e:
		perror(str(e))
		return False
	
	return True
		

def run():
	# retrieve settings for command-line options
	options, args = parseOptions()
	if not checkOptions(options):
		return

	print(options)
	print(args)

