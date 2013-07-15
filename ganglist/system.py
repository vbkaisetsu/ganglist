# -*- coding: utf-8; indent-tabs-mode: t; tab-width: 4 -*-
#
# system.py
#


import curses
from datetime import datetime
import time
from xml.etree import ElementTree
from ganglist.utils import Utils

from gettext import gettext as _
from gettext import ngettext

class System:


	__TIMEOUT = 10


	@staticmethod
	def __timeScaleToStep(timescale, chartWidth):
		if timescale == 0:
			return 1800 / chartWidth # 30 mins
		elif timescale == 1:
			return 7200 / chartWidth # 2 hours
		elif timescale == 2:
			return 43200 / chartWidth # 12 hours
		elif timescale == 3:
			return 345600 / chartWidth # 4 days
		elif timescale == 4:
			return 2592000 / chartWidth # 30 days
		else:
			raise ValueError


	@staticmethod
	def __secondsToStr(seconds):
		if seconds < 1:
			raise ValueError
		if seconds < 60:
			return ngettext('%d second', '%d seconds', seconds) % seconds
		seconds //= 60
		if seconds < 60:
			return ngettext('%d minute', '%d minutes', seconds) % seconds
		seconds //= 60
		if seconds < 24:
			return ngettext('%d hour', '%d hours', seconds) % seconds
		seconds //= 24
		return ngettext('%d day', '%d days', seconds) % seconds


	@staticmethod
	def __getProcData(filename):
		fp = open(filename, "r")
		lst = []
		for l in fp:
			spl = l.split()
			spl[2] = spl[2].split("/")[-1]
			lst.append(spl)
		return lst


	# parse xml files dumped from rrds
	@staticmethod
	def __getRRD(filename):
		tree = ElementTree.parse(filename)
		elem = tree.getroot()
		rootstep = int(elem.find(".//step").text)
		lastupdate = int(elem.find(".//lastupdate").text)
		dataset = {}
		for e in elem.findall(".//rra"):
			step = int(e.find(".//pdp_per_row").text) * rootstep
			dataset.update({lastupdate - i * step: Utils.safeFloat(val.text) for i, val in enumerate(reversed(e.findall(".//v")))})
		return sorted(dataset.items(), key=lambda x: x[0])


	@staticmethod
	def __getRRDValue(data, time, period):
		valsum = 0
		cnt = 0
		for i in range(len(data)):
			if time - period <= data[i][0]:
				cnt += 1
				valsum += data[i][1]
				if time <= data[i][0]:
					return valsum / cnt
		return data[-1][1]


	def __init__(self, options, env):
		self.__options = options
		self.__env = env

		self.__chart_h = self.__options.height
		self.__chart_w = self.__options.width
		self.__showusers = self.__options.showusers


	def __initial(self):
		self.__window = curses.initscr()
		curses.noecho()
		curses.cbreak()
		curses.raw()
		self.__window.keypad(1)
		self.__window.timeout(System.__TIMEOUT)

		self.__timescale = 0
		self.__timer = 0
		self.__mpp = 0
		self.__page = 0
		self.__redraw = False

		self.__cpu_num = {}
		self.__cpu_speed = {}
		self.__cpu_user = {}
		self.__cpu_system = {}

		self.__mem_buffers = {}
		self.__mem_cached = {}
		self.__mem_free = {}
		self.__mem_total = {}

		self.__cpu_topuser = {}
		self.__mem_topuser = {}

		self.__h = 0
		self.__w = 0


	def __final(self):
		self.__window.keypad(0)
		curses.noraw()
		curses.nocbreak()
		curses.echo()
		curses.endwin()


	def __printFooter(self, text):
		self.__window.addstr(self.__h - 1, 0, ' ' * (self.__w - 1))
		self.__window.addstr(self.__h - 1, 1, text)


	def __refresh(self):
		self.__window.move(self.__h - 1, 0)
		self.__window.refresh()


	# get machines per page
	def __initPage(self):
		i = 0
		self.__h, self.__w = self.__window.getmaxyx()

		needed_h = self.__chart_h + (3 if self.__showusers else 0) + 5
		needed_w = self.__chart_w * 2 + 3

		if self.__h < needed_h + 2 or self.__w < needed_w:
			return False

		for starty in range(0, self.__h - needed_h + 1, needed_h):
			for startx in range(0, self.__w - needed_w + 1, needed_w + 2):
				i += 1
				if i == len(self.__env.HOSTS):
					break
			if i == len(self.__env.HOSTS):
				break

		if self.__mpp != i:
			self.__mpp = i
			self.__page = 0
		self.__redraw = True

		return True


	def __keystroke(self):
		key = self.__window.getch();

		# Q: quit
		if key == ord('q'):
			return False

		# U: force update
		if key == ord('u'):
			self.__timer = 0

		# Resize
		elif key == curses.KEY_RESIZE:
			if not self.__initPage():
				return False

		# Down: next page
		elif key == curses.KEY_DOWN:
			if self.__mpp * (self.__page + 1) < len(self.__env.HOSTS):
				self.__page += 1
				self.__redraw = True

		# Up: previous page
		elif key == curses.KEY_UP:
			if self.__page > 0:
				self.__page -= 1
				self.__redraw = True

		# Left: zoom-out
		elif key == curses.KEY_LEFT:
			if self.__timescale < 4:
				self.__timescale += 1
				self.__redraw = True

		# Right: zoom-in
		elif key == curses.KEY_RIGHT:
			if self.__timescale > 0:
				self.__timescale -= 1
				self.__redraw = True

		return True


	def __elapse(self):
		if self.__timer == 0:
			for m in self.__env.HOSTS:
				self.__printFooter(_("Loading ..."))
				self.__refresh()
				try:
					self.__cpu_num[m] = Utils.safeInt(System.__getRRD("%s/%s/cpu_num.rrd" % (self.__env.DATADIR, m))[-1][1])
					self.__cpu_speed[m] = Utils.safeFloat(System.__getRRD("%s/%s/cpu_speed.rrd" % (self.__env.DATADIR, m))[-1][1])
					self.__cpu_user[m] = System.__getRRD("%s/%s/cpu_user.rrd" % (self.__env.DATADIR, m))
					self.__cpu_system[m] = System.__getRRD("%s/%s/cpu_system.rrd" % (self.__env.DATADIR, m))

					self.__mem_buffers[m] = System.__getRRD("%s/%s/mem_buffers.rrd" % (self.__env.DATADIR, m))
					self.__mem_cached[m] = System.__getRRD("%s/%s/mem_cached.rrd" % (self.__env.DATADIR, m))
					self.__mem_free[m] = System.__getRRD("%s/%s/mem_free.rrd" % (self.__env.DATADIR, m))
					self.__mem_total[m] = System.__getRRD("%s/%s/mem_total.rrd" % (self.__env.DATADIR, m))

					self.__cpu_topuser[m] = System.__getProcData("%s/%s/cpu_topuser" % (self.__env.DATADIR, m))
					self.__mem_topuser[m] = System.__getProcData("%s/%s/mem_topuser" % (self.__env.DATADIR, m))
				except ElementTree.ParseError:
					return False
				except IOError:
					return False

			self.__redraw = True

		# go ahead
		self.__timer += 1
		if self.__timer >= self.__options.interval * 1000 // System.__TIMEOUT:
			self.__timer = 0

		return True


	def __drawStatus(self, x, y, current, step, hostname):

		# variables
		cpu_user    = self.__cpu_user[hostname]
		cpu_system  = self.__cpu_system[hostname]
		cpu_num     = self.__cpu_num[hostname]
		cpu_speed   = self.__cpu_speed[hostname]
		cpu_topuser = self.__cpu_topuser[hostname]
		mem_free    = self.__mem_free[hostname]
		mem_buffers = self.__mem_buffers[hostname]
		mem_cached  = self.__mem_cached[hostname]
		mem_total   = self.__mem_total[hostname]
		mem_topuser = self.__mem_topuser[hostname]

		# utilities
		hspace = ' ' * self.__chart_w
		hline = '-' * self.__chart_w
		hsharp = '#' * self.__chart_w
		rowText = lambda l, r, sep: sep + l + sep + r + sep # ex. '|@@@@|####|'

		cpu_title = "cpu (%d * %sHz)" % (cpu_num, (("%.1fG" % (cpu_speed / 1000)) if cpu_speed >= 1000 else ("%.1fM" % cpu_speed)))
		mem_title = "mem (%siB)" % (("%.1fG" % (mem_total[-1][1] / 1024 / 1024)) if mem_total[-1][1] >= 1024 else ("%.1fM" % (mem_total[-1][1] / 1024)))
		cpu_title = cpu_title[:self.__chart_w]
		mem_title = mem_title[:self.__chart_w]

		self.__window.addstr(y + 1, x, rowText(hspace, hspace, ' '))
		self.__window.addstr(y + 1, x + 1, cpu_title.center(self.__chart_w))
		self.__window.addstr(y + 1, x + self.__chart_w + 2, mem_title.center(self.__chart_w))
		self.__window.addstr(y + 2, x, rowText(hline, hline, '|'))

		for i in range(self.__chart_h):
			self.__window.addstr(y + 3 + i, x, rowText(hspace, hsharp, '|'))

		self.__window.addstr(y + 3 + self.__chart_h, x, rowText(hline, hline, '|'))

		for j in range(self.__chart_w):
			val1 = System.__getRRDValue(cpu_system, current + (j - self.__chart_w + 1) * step, step)
			val2 = System.__getRRDValue(cpu_user, current + (j - self.__chart_w + 1) * step, step)
			if val1 < 0 or val2 < 0:
				for i in range(self.__chart_h):
					self.__window.addstr(y + 3 + i, x + 1 + j, "?")
				continue
			val2 += val1

			for i in range(self.__chart_h):
				if val2 > i / self.__chart_h * 100:
					self.__window.addstr(y + self.__chart_h + 2 - i, x + 1 + j, "#")
			for i in range(self.__chart_h):
				if val1 > i / self.__chart_h * 100:
					self.__window.addstr(y + self.__chart_h + 2 - i, x + 1 + j, "@")

		i = 0

		if self.__showusers:
			self.__window.addstr(y + 4 + self.__chart_h, x, rowText(hspace, hspace, '|'))
			self.__window.addstr(y + 5 + self.__chart_h, x, rowText(hspace, hspace, '|'))
			self.__window.addstr(y + 6 + self.__chart_h, x, rowText(hline, hline, '|'))

			for u in cpu_topuser:
				mu = u[:]
				mu[1] += "%"
				mu[2] = mu[2].split("/")[-1]
				s = " ".join(mu)
				self.__window.addstr(y + self.__chart_h + 4 + i, x + 2, s[:self.__chart_w - 2])
				i += 1

		for j in range(self.__chart_w):
			total = System.__getRRDValue(mem_total, current + (j - self.__chart_w + 1) * step, step)
			val1 = System.__getRRDValue(mem_free, current + (j - self.__chart_w + 1) * step, step)
			val2 = System.__getRRDValue(mem_cached, current + (j - self.__chart_w + 1) * step, step)
			val3 = System.__getRRDValue(mem_buffers, current + (j - self.__chart_w + 1) * step, step)
			if total < 0 or val1 < 0 or val2 < 0 or val3 < 0:
				for i in range(self.__chart_h):
					self.__window.addstr(y + 3 + i, x + self.__chart_w + 2 + j, "?")
				continue

			val1 /= total
			val2 = val1 + (val2 + val3) / total

			for i in range(self.__chart_h):
				if val2 >= i / self.__chart_h:
					self.__window.addstr(y + 3 + i, x + self.__chart_w + 2 + j, ".")
			for i in range(self.__chart_h):
				if val1 >= i / self.__chart_h:
					self.__window.addstr(y + 3 + i, x + self.__chart_w + 2 + j, " ")

		i = 0

		if self.__showusers:
			for u in mem_topuser:
				mu = u[:]
				mu[1] += "%"
				mu[2] = mu[2].split("/")[-1]
				s = " ".join(mu)
				self.__window.addstr(y + self.__chart_h + 4 + i, x + self.__chart_w + 3, s[:self.__chart_w - 2])
				i += 1


	def __drawBoxes(self, now, step):
		needed_h = self.__chart_h + (3 if self.__showusers else 0) + 5
		needed_w = self.__chart_w * 2 + 3

		hn = self.__mpp * self.__page

		for starty in range(0, self.__h - needed_h - 1, needed_h):
			for startx in range(0, self.__w - needed_w + 1, needed_w + 2):
				hostname = self.__env.HOSTS[hn]

				#self.__window.addstr(starty + 0, startx, " " * needed_w)
				self.__window.addstr(starty + 0, startx, hostname.center(needed_w))

				step = System.__timeScaleToStep(self.__timescale, self.__chart_w)

				# each statuses
				self.__drawStatus(startx, starty, now, step, hostname)

				hn += 1
				if hn == len(self.__env.HOSTS):
					break

			if hn == len(self.__env.HOSTS):
				break

		uy = starty + self.__chart_h + (3 if self.__showusers else 0) + 5
		self.__window.addstr(uy, 1, "[ # ] user  [ @ ] sys")
		self.__window.addstr(uy, self.__chart_w + 2, "[ # ] user  [ . ] cache/buff")


	def __drawInlines(self, now, step):
		self.__window.addstr(0, 0, 'Sorry, this option is not implemented yet.');


	def __draw(self):
		self.__window.erase()

		now = int(time.mktime(datetime.now().timetuple()))
		now -= now % 60
		step = System.__timeScaleToStep(self.__timescale, self.__chart_w)
		start = now - step * self.__chart_w

		if self.__options.inline:
			self.__drawInlines(now, step)
		else:
			self.__drawBoxes(now, step)

		startstr = datetime.fromtimestamp(start).strftime('%Y-%m-%d %H:%M:%S')
		nowstr = datetime.fromtimestamp(now).strftime('%Y-%m-%d %H:%M:%S')
		stepstr = System.__secondsToStr(step * self.__chart_w)

		self.__printFooter("%s - %s (%s)" % (startstr, nowstr, stepstr))
		self.__refresh()


	def __mainloop(self):

		firstloop = True

		while True:
			self.__redraw = False

			# initial update
			if firstloop:
				firstloop = False
				if not self.__initPage():
					return

			# process key stroke
			if not self.__keystroke():
				return

			try:
				# update
				if not self.__elapse():
					return

				# redraw
				if self.__redraw:
					self.__draw()
			except curses.error:
				# when resizing occured with drawing the screen,
				# the program throws this error.
				# since the screen will be refreshed when receiving next KEY_RESIZE message,
				# this error may be ignored.
				pass


	def run(self):
		self.__initial()
		self.__mainloop()
		self.__final()

