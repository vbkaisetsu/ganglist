# -*- coding: utf-8; indent-tabs-mode: t; tab-width: 4 -*-
#
# system.py
#


import time
from datetime import datetime
from xml.etree import ElementTree

from gettext import gettext as _
from gettext import ngettext

from ganglist.utils import Utils
from ganglist.data import Data
from ganglist.screen import Screen


class System:


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
	

	def __init__(self, options, env, colorMap):
		self.__options = options
		self.__env = env
		self.__colorMap = colorMap

		self.__chart_h = self.__options.height
		self.__chart_w = self.__options.width
		self.__showusers = self.__options.showusers


	def __initial(self):
		self.__scr = Screen(self.__options.coloring, self.__colorMap)

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


	def __final(self):
		self.__scr.final()
		self.__scr = None


	# get machines per page
	def __initPage(self):
		i = 0

		needed_h = self.__chart_h + (3 if self.__showusers else 0) + 5
		needed_w = self.__chart_w * 2 + 3

		if self.__scr.height() < needed_h + 2 or self.__scr.width() < needed_w:
			return False

		for starty in range(0, self.__scr.height() - needed_h + 1, needed_h):
			for startx in range(0, self.__scr.width() - needed_w + 1, needed_w + 2):
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
		key = self.__scr.getch();

		# Q: quit
		if key == ord('q'):
			return False

		# U: force update
		if key == ord('u'):
			self.__timer = 0

		# Resize
		elif key == 'RESIZE':
			if not self.__initPage():
				return False

		# Down: next page
		elif key == 'DOWN':
			if self.__mpp * (self.__page + 1) < len(self.__env.HOSTS):
				self.__page += 1
				self.__redraw = True

		# Up: previous page
		elif key == 'UP':
			if self.__page > 0:
				self.__page -= 1
				self.__redraw = True

		# Left: zoom-out
		elif key == 'LEFT':
			if self.__timescale < 4:
				self.__timescale += 1
				self.__redraw = True

		# Right: zoom-in
		elif key == 'RIGHT':
			if self.__timescale > 0:
				self.__timescale -= 1
				self.__redraw = True

		return True


	def __elapse(self):
		if self.__timer == 0:
			for m in self.__env.HOSTS:
				self.__scr.writeFooter(_("Loading ..."))
				self.__scr.refresh()
				try:
					self.__cpu_num[m] = Utils.safeInt(Data.getRRD("%s/%s/cpu_num.rrd" % (self.__env.DATADIR, m))[-1][1])
					self.__cpu_speed[m] = Utils.safeFloat(Data.getRRD("%s/%s/cpu_speed.rrd" % (self.__env.DATADIR, m))[-1][1])
					self.__cpu_user[m] = Data.getRRD("%s/%s/cpu_user.rrd" % (self.__env.DATADIR, m))
					self.__cpu_system[m] = Data.getRRD("%s/%s/cpu_system.rrd" % (self.__env.DATADIR, m))

					self.__mem_buffers[m] = Data.getRRD("%s/%s/mem_buffers.rrd" % (self.__env.DATADIR, m))
					self.__mem_cached[m] = Data.getRRD("%s/%s/mem_cached.rrd" % (self.__env.DATADIR, m))
					self.__mem_free[m] = Data.getRRD("%s/%s/mem_free.rrd" % (self.__env.DATADIR, m))
					self.__mem_total[m] = Data.getRRD("%s/%s/mem_total.rrd" % (self.__env.DATADIR, m))

					self.__cpu_topuser[m] = Data.getProcData("%s/%s/cpu_topuser" % (self.__env.DATADIR, m))
					self.__mem_topuser[m] = Data.getProcData("%s/%s/mem_topuser" % (self.__env.DATADIR, m))
				except ElementTree.ParseError:
					return False
				except IOError:
					return False

			self.__redraw = True

		# go ahead
		self.__timer += 1
		if self.__timer >= self.__options.interval * 1000 // Screen.timeout():
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
		rowText = lambda l, r, sep: sep + l + sep + r + sep # ex. '|@@@@|####|'

		cpu_title = "cpu (%d * %sHz)" % (cpu_num, (("%.1fG" % (cpu_speed / 1000)) if cpu_speed >= 1000 else ("%.1fM" % cpu_speed)))
		mem_title = "mem (%siB)" % (("%.1fG" % (mem_total[-1][1] / 1024 / 1024)) if mem_total[-1][1] >= 1024 else ("%.1fM" % (mem_total[-1][1] / 1024)))
		cpu_title = cpu_title[:self.__chart_w]
		mem_title = mem_title[:self.__chart_w]

		self.__scr.write(y + 1, x, rowText(hspace, hspace, ' '))
		self.__scr.write(y + 1, x + 1, cpu_title.center(self.__chart_w))
		self.__scr.write(y + 1, x + self.__chart_w + 2, mem_title.center(self.__chart_w))
		self.__scr.write(y + 2, x, rowText(hline, hline, '|'))

		for i in range(self.__chart_h):
			self.__scr.write(y + 3 + i, x, rowText(hspace, hspace, '|'))
			
		self.__scr.write(y + 3 + self.__chart_h, x, rowText(hline, hline, '|'))
		
		for j in range(self.__chart_w):
			val1 = Data.getRRDValue(cpu_system, current + (j - self.__chart_w + 1) * step, step)
			val2 = Data.getRRDValue(cpu_user, current + (j - self.__chart_w + 1) * step, step)
			if val1 < 0 or val2 < 0:
				for i in range(self.__chart_h):
					self.__scr.write(y + 3 + i, x + 1 + j, "?")
				continue
			val2 += val1

			for i in range(self.__chart_h):
				if val2 > i / self.__chart_h * 100:
					self.__scr.write(y + self.__chart_h + 2 - i, x + 1 + j, "#", 'USER')
			for i in range(self.__chart_h):
				if val1 > i / self.__chart_h * 100:
					self.__scr.write(y + self.__chart_h + 2 - i, x + 1 + j, "@", 'SYSTEM')

		i = 0

		if self.__showusers:
			self.__scr.write(y + 4 + self.__chart_h, x, rowText(hspace, hspace, '|'))
			self.__scr.write(y + 5 + self.__chart_h, x, rowText(hspace, hspace, '|'))
			self.__scr.write(y + 6 + self.__chart_h, x, rowText(hline, hline, '|'))

			for u in cpu_topuser:
				mu = u[:]
				mu[1] += "%"
				mu[2] = mu[2].split("/")[-1]
				s = " ".join(mu)
				self.__scr.write(y + self.__chart_h + 4 + i, x + 2, s[:self.__chart_w - 2])
				i += 1

		for j in range(self.__chart_w):
			total = Data.getRRDValue(mem_total, current + (j - self.__chart_w + 1) * step, step)
			val1 = Data.getRRDValue(mem_free, current + (j - self.__chart_w + 1) * step, step)
			val2 = Data.getRRDValue(mem_cached, current + (j - self.__chart_w + 1) * step, step)
			val3 = Data.getRRDValue(mem_buffers, current + (j - self.__chart_w + 1) * step, step)
			if total < 0 or val1 < 0 or val2 < 0 or val3 < 0:
				for i in range(self.__chart_h):
					self.__scr.write(y + 3 + i, x + self.__chart_w + 2 + j, "?")
				continue

			used = (total - val1) / total
			active = used - (val2 - val3) / total
			
			for i in range(self.__chart_h):
				r = (self.__chart_h - i) / self.__chart_h
				if r < active:
					self.__scr.write(y + 3 + i, x + self.__chart_w + 2 + j, "#", 'USER')
				elif r < used:
					self.__scr.write(y + 3 + i, x + self.__chart_w + 2 + j, ".", 'CACHE')
	
		i = 0

		if self.__showusers:
			for u in mem_topuser:
				mu = u[:]
				mu[1] += "%"
				mu[2] = mu[2].split("/")[-1]
				s = " ".join(mu)
				self.__scr.write(y + self.__chart_h + 4 + i, x + self.__chart_w + 3, s[:self.__chart_w - 2])
				i += 1


	def __drawBoxes(self, now, step):
		needed_h = self.__chart_h + (3 if self.__showusers else 0) + 5
		needed_w = self.__chart_w * 2 + 3

		hn = self.__mpp * self.__page

		for starty in range(0, self.__scr.height() - needed_h - 1, needed_h):
			for startx in range(0, self.__scr.width() - needed_w + 1, needed_w + 2):
				hostname = self.__env.HOSTS[hn]

				self.__scr.write(starty + 0, startx, hostname.center(needed_w))

				step = System.__timeScaleToStep(self.__timescale, self.__chart_w)

				# each statuses
				self.__drawStatus(startx, starty, now, step, hostname)

				hn += 1
				if hn == len(self.__env.HOSTS):
					break

			if hn == len(self.__env.HOSTS):
				break

		uy = starty + self.__chart_h + (3 if self.__showusers else 0) + 5
		self.__scr.write(uy, 1, '[ # ]', 'USER')
		self.__scr.write(uy, 1 + 6, 'user')
		self.__scr.write(uy, 1 + 12, '[ @ ]', 'SYSTEM')
		self.__scr.write(uy, 1 + 18, 'sys')
		self.__scr.write(uy, self.__chart_w + 2, "[ # ]", 'USER')
		self.__scr.write(uy, self.__chart_w + 2 + 6, "user")
		self.__scr.write(uy, self.__chart_w + 2 + 12, "[ . ]", 'CACHE')
		self.__scr.write(uy, self.__chart_w + 2 + 18, "cache/buff")
	

	def __drawInlines(self, now, step):
		self.__scr.write(0, 0, 'Sorry, this option is not implemented yet.');


	def __draw(self):
		self.__scr.erase()

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

		self.__scr.writeFooter("%s - %s (%s)" % (startstr, nowstr, stepstr))
		self.__scr.refresh()


	def __mainloop(self):

		self.__redraw = False

		# initial update
		if not self.__initPage():
			return

		while True:
			# process key stroke
			if not self.__keystroke():
				break

			# update
			if not self.__elapse():
				break

			# redraw
			if self.__redraw:
				self.__draw()
				self.__redraw = False


	def run(self):
		self.__initial()
		self.__mainloop()
		self.__final()

