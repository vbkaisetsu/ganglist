# -*- coding: utf-8; indent-tabs-mode: t; tab-width: 4 -*-
#
# utils.py
#


class Utils:


	# print error message.
	@staticmethod
	def perror(text):
		import sys
		sys.stderr.write('ERROR: '+text+'\n')


	# convert some data into corresponding integer value
	# or -1 if cannot.
	@staticmethod
	def safeInt(data):
		try:
			return int(data)
		except ValueError:
			return -1

	# convert some data into corresponding float value
	# or -1.0 if cannot.
	@staticmethod
	def safeFloat(data):
		try:
			return float(data)
		except ValueError:
			return -1.0


# He is our cool master
# Please read the following code as a document.
class Neubig:

	logo_right = [
		'               .i   l,                          ',
		'  ;G,:@Cf     iG    .:LG;, lC;.          f;     ',
		'   tl@,;@@G,L                     ,ft           ',
		'      if      ,li           :;;:, ;fl.,. .lGGt  ',
		'         t@ftG@CGL;    tit..tfC@,               ',
		'    ;G.    ;G@G,             LfG@@  tG@C     C  ',
		' C@@@l.G@t          ,iiii     ::  .   .C        ',
		'               .   ,C@@Gtilft;iCGG.tt,lGt,      ',
		'              C; Lff@@G@G@tG;@f                 ',
		'  C lCftL@L,       .@LG;         l:        C;   ',
		'  ff@llC@G@l                  fC@@GC.f:         ',
		'        .G;      tfC., ,,    fC.t        Ct@.   ',
		'     .ttGCf@@G.                 ;it             ',
		'     L.      L;              ,,ttt,i   ;CG; :G; ',
		' f:C t@@Gi     ,@@@G@@   ft      t@GC@ ,G       ',
		'                        ...  .lLCf.             ',
		'              ;f G@@GGCG@@@@.,,                 ',
		'  tt@;L fl         .@CG@l     :llG        il    ',
		'   ;CGCf@@@Gti                   .tflf;         ',
		'       fl      .G:           L:  ,G:     .,:G   ',
		'        t@,iCff l              GG.              ',
		'     C      :C:.                 lGG::.@C.   L  ',
		' Lf@L:C@Gi      :;lfCCflfi       ;@ftt f.       ',
		'                     ,lC@@@@@@@G@G@@G@G,        ',
		'          tLGGLL@@Gi;lGfl@@@@,L;                ',
		'  ,LLGt  tC@Gi       .           ii   :;    ti  ',
		' ;t@@lClGL;                   .@C;    G         ',
		'         .tCfi;;;i@@G@GCG;fLf@@GL      .CLC.    ',
		'     fGt;@C@GG:                    C;           ',
		'     it       C.            ;GG@G   l@@C C@ C@l ',
		' ifC l@G@,    .Cf:.       it     ,;;;,  ;l      ',
		'                                ,.              ',
	]

	logo_left = [
		'                          ,l   i.               ',
		'     ;f          .;Cl ,;GL:.    Ci     fC@:,G;  ',
		'           tf,                     L,G@@;,@lt   ',
		'  tGGl. .,.lf; ,:;;:           il,      fi      ',
		'               ,@Cft..tit    ;LGC@Gtf@t.        ',
		'  C     C@Gt  @@GfL             ,G@G;    .G;    ',
		'        C.   .  ::     iiii,          t@G.l@@@C ',
		'      ,tGl,tt.GGCi;tflitG@@C,   .               ',
		'                 f@;Gt@G@G@@ffL ;C              ',
		'   ;C        :l         ;GL@.       ,L@LtfCl C  ',
		'         :f.CG@@Cf                  l@G@Cll@ff  ',
		'   .@tC        t.Cf    ,, ,.Gft      ;G.        ',
		'             ti;                 .G@@fCCtt.     ',
		' ;G: ;GCi   i,ttt,,              ;L      .L     ',
		'       C: @CG@t      tf   @@G@@@:     iG@@t C:f ',
		'             .fCLl.  ...                        ',
		'                 ,,.@G@@GCGG@@G f;              ',
		'    li        Gll:     l@GC@.         lf L;@tf  ',
		'          ;flft.                   itG@@@fCGC;  ',
		'   G:,.     :G,  :L           :G.      if       ',
		'              .GG              l ffCl,@f        ',
		'  L   .C@.::GGl                 .;C:      C     ',
		'       .f ttf@;       iflfCCfl;:      iG@C:L@fL ',
		'        ,G@G@@G@G@@@@@@@Cl,                     ',
		'                ;L,@@@@lfGl;iG@@LLGGLf          ',
		'  it    ;:   ii           .       iG@Ct  tGLL,  ',
		'         G    ;C@.                   ;LGlLl@@t; ',
		'    .LLC.      LG@@fLf;GCG@G@@i;;;ifCt.         ',
		'            ;C                    :G@@C@;tGf    ',
		' l@C @C C@@l   G@GG;            .C       tl     ',
		'      l;  ,;;;,     ti       .:fC.    ,@G@l Cfi ',
		'              .,                                ',
	]


	def suffle(data):
		array = [0] * 32
		for i in range(32):
			t = i
			k = 0
			for j in range(5):
				k = (k << 1) + (t & 1)
				t >>= 1
			array[k] = data[i]
		return array


	def main():
		import curses, random, math
		
		tau = 0.003
		
		logo_left = Neubig.suffle(Neubig.logo_left)
		logo_right = Neubig.suffle(Neubig.logo_right)
		
		window = curses.initscr() 
		curses.noecho()
		window.keypad(1)
		curses.cbreak()
		curses.raw()

		window.timeout(20)

		h, w = window.getmaxyx()

		state = 0
		x = -47
		y = int((h - 33) / 2)
		
		t = 0

		logo = logo_right

		while True:
			thr = 0.5 * (1 - math.exp(-tau * t))
			key = window.getch();
			if key == curses.KEY_RESIZE:
				h, w = window.getmaxyx()
				y = int((h - 33) / 2)
				if y < 0:
					y = 0
				window.clear()

			for i, line in enumerate(logo):
				if y + i < 0:
					continue
				if h <= y + i + 1:
					break
				if x < 0:
					window.addstr(y + i, 0, line[-x:w-x])
				else:
					window.addstr(y + i, x, line[0:w-x])

			if 0 <= x and x < w - 47:
				t += 1
				rnd = random.random()
				if state == 0:
					if rnd < thr:
						state = 1
						t = 0
				elif state == 1:
					if rnd < thr:
						state = 0
					elif rnd > 1 - thr:
						state = 2
						t = 0
				else:
					if rnd < thr:
						state = 1
						t = 0

			if state == 0:
				x += 1
				logo = logo_right

			if state == 2:
				x -= 1
				logo = logo_left

			if x == w or x == -47:
				break

			window.move(h - 1, 0)

		curses.noraw()
		curses.nocbreak()
		window.keypad(0)
		curses.echo()
		curses.endwin()
