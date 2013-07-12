# -*- coding: utf-8; indent-tabs-mode: t; tab-width: 4 -*-
#
# main.py
#

from settings import Options
import utils
from utils import *
from system import System


# parse options
def parseOptions():
	from optparse import OptionParser, SUPPRESS_HELP

	q = OptionParser(epilog="""
This GangList has my master's powers.
""")

	# add options into parser
	q.add_option('-W', '--width', dest='width',
		default=str(Options.DEFAULT_WIDTH),
		help='graph width (default: %d)' % Options.DEFAULT_WIDTH,
		metavar='<INT>')
	q.add_option('-H', '--height', dest='height',
		default=str(Options.DEFAULT_HEIGHT),
		help='graph height (default: %d)' % Options.DEFAULT_HEIGHT,
		metavar='<INT>')
	q.add_option('-U', '--withusers', action="store_true", dest='showusers',
		default=bool(Options.DEFAULT_SHOWUSERS),
		help='enable user list (default: %s)' % str(Options.DEFAULT_SHOWUSERS))
	q.add_option('-N', '--nouser', action="store_false", dest='showusers',
		default=bool(Options.DEFAULT_SHOWUSERS),
		help='disable user list (default: %s)' % str(not Options.DEFAULT_SHOWUSERS))
	
	# eggs
	q.add_option('--neubig', dest='neubig',
		action='store_true', default=False, help=SUPPRESS_HELP)
	q.add_option('--right', dest='right',
		action='store_true', default=False, help=SUPPRESS_HELP)
	q.add_option('--walk', dest='walk',
		action='store_true', default=False, help=SUPPRESS_HELP)
	
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
		Utils.perror(str(e))
		return False
	
	return True
		

def run():
	# retrieve settings for command-line options
	options, args = parseOptions()
	if not checkOptions(options):
		return

	if options.neubig:
		if options.walk:
			Neubig.walk()
		elif options.right:
			Neubig.rstand()
		else:
			Neubig.stand()
	else:
		sys = System(options)
		sys.run()

