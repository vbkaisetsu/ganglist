# -*- coding: utf-8; indent-tabs-mode: t; tab-width: 4 -*-
#
# main.py
#

from settings import Options
from utils import Utils
import system


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
	
	# eggs
	q.add_option('--neubig', dest='neubig',
		action='store_true', default=False)
	
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
		Neubig.main()
	else:
		system.main(options)






































































class Neubig:
	def main():
		print('''
              .i   l,
             ;f G@@GGCG@@@@.,,
             C; Lff@@G@G@tG;@f
         tLGGLL@@Gi;lGfl@@@@,L;
        t@ftG@CGL;    tit..tfC@,
       t@,iCff l              GG.
    .ttGCf@@G.                 ;it
   fGt;@C@GG:                    C;
  tl@,;@@G,L                     ,ft
 ;CGCf@@@Gti                   .tflf;
 ff@llC@G@l                  fC@@GC.f:
;t@@lClGL;                   .@C;    G
C@@@l.G@t          ,iiii     ::  .   .C
Lf@L:C@Gi      :;lfCCflfi       ;@ftt f.
f:C t@@Gi     ,@@@G@@   ft      t@GC@ ,G
ifC l@G@,    .Cf:.       it     ,;;;,  ;l
 ;G,:@Cf     iG    .:LG;, lC;.          f;
 tt@;L fl         .@CG@l     :llG        il
 C lCftL@L,       .@LG;         l:        C;
 ,LLGt  tC@Gi       .           ii   :;    ti
   ;G.    ;G@G,             LfG@@  tG@C     C
    C      :C:.                 lGG::.@C.   L
    L.      L;              ,,ttt,i   ;CG; :G;
    it       C.            ;GG@G   l@@C C@ C@l
     if      ,li           :;;:, ;fl.,. .lGGt
      fl      .G:           L:  ,G:     .,:G
       .G;      tfC., ,,    fC.t        Ct@.
        .tCfi;;;i@@G@GCG;fLf@@GL      .CLC.
              .   ,C@@Gtilft;iCGG.tt,lGt,
                    ,lC@@@@@@@G@G@@G@G,
                       ...  .lLCf.
                               ,.
''')


