# -*- coding: utf-8; indent-tabs-mode: t; tab-width: 4 -*-
#
# main.py
#

from ganglist.settings import Settings
from ganglist import utils
from ganglist.utils import *
from ganglist.system import System


# parse options
def parseOptions(defaultOptions):
	from optparse import OptionParser, SUPPRESS_HELP

	q = OptionParser(epilog="""
This GangList has my master's powers.
""")

	# add options into parser
	q.add_option('-W', '--width', dest='width',
		default=str(defaultOptions.DEFAULT_WIDTH),
		help='graph width (default: %d)' % defaultOptions.DEFAULT_WIDTH,
		metavar='<INT>')
	q.add_option('-H', '--height', dest='height',
		default=str(defaultOptions.DEFAULT_HEIGHT),
		help='graph height (default: %d)' % defaultOptions.DEFAULT_HEIGHT,
		metavar='<INT>')
	q.add_option('-u', '--withusers', action="store_true", dest='showusers',
		default=bool(defaultOptions.DEFAULT_SHOWUSERS),
		help='enable user list explicitly')
	q.add_option('-n', '--nouser', action="store_false", dest='showusers',
		default=bool(defaultOptions.DEFAULT_SHOWUSERS),
		help='disable user list explicitly')
	q.add_option('-l', '--inline', action='store_true', dest='inline',
		default=bool(defaultOptions.DEFAULT_INLINE),
		help='inline view')
	q.add_option('-t', '--interval', dest='interval',
		default=str(defaultOptions.DEFAULT_INTERVAL),
		help='update interval [seconds] (default: %d)' % defaultOptions.DEFAULT_INTERVAL,
		metavar='<INT>')

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
def checkOptions(options, defaultOptions):

	def forceInt(options, name):
		val = getattr(options, name)
		if not val.isdigit():
			raise ValueError('Option "%s" must be integer.' % name)
		setattr(options, name, int(val))
	
	def forceBool(options, name):
		setattr(options, name, bool(getattr(options, name)))

	def assertRange(options, name, minval, maxval):
		val = getattr(options, name)
		if val < minval or val > maxval:
			raise ValueError('Option "%s" must be: %d <= %s <= %d.' % (name, minval, name, maxval))
	
	try:
		forceInt(options, 'width')
		forceInt(options, 'height')
		forceInt(options, 'interval')
		forceBool(options, 'showusers')
		forceBool(options, 'neubig')
		forceBool(options, 'right')
		forceBool(options, 'walk')
		assertRange(options, 'width', defaultOptions.MIN_WIDTH, defaultOptions.MAX_WIDTH)
		assertRange(options, 'height', defaultOptions.MIN_HEIGHT, defaultOptions.MAX_HEIGHT)
		assertRange(options, 'interval', defaultOptions.MIN_INTERVAL, defaultOptions.MAX_INTERVAL)
	except ValueError as e:
		Utils.perror(str(e))
		return False
	
	return True
		

def run():
	# retrieve settings for command-line options
	settings = Settings()
	
	if not settings.environment.HOSTS:
		return

	options, args = parseOptions(settings.options)
	if not checkOptions(options, settings.options):
		return

	if options.neubig:
		if options.walk:
			Neubig.walk()
		elif options.right:
			Neubig.rstand()
		else:
			Neubig.stand()
	else:
		sys = System(options, settings.environment)
		sys.run()

