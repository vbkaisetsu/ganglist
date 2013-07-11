# -*- coding: utf-8; indent-tabs-mode: t; tab-width: 4 -*-
#
# system.py
#


import curses
from datetime import datetime
import time
from xml.etree import ElementTree
from settings import Environment as Env
from utils import Utils


class System:
	

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


	def __init__(self, options):
		self.__options = options
	

	def __initial(self):
		self.__window = curses.initscr()
		curses.noecho()
		curses.cbreak()
		self.__window.keypad(1)
		self.__window.timeout(10)

		self.__timescale = 0
		self.__timer = 0
		self.__mpp = 0
		self.__page = 0
		self.__firstloop = True
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
		curses.nocbreak()
		self.__window.keypad(0)
		curses.echo()
		curses.endwin()
	

	def __keystroke(self):
		key = self.__window.getch();

		# Q: Quit
		if key == ord("q"):
			return False
		
		# Resize
		elif key == curses.KEY_RESIZE or self.__firstloop:
			# get machines per page
			i = 0
			self.__h, self.__w = self.__window.getmaxyx()
			if self.__h < 15 or self.__w < 63:
				return False
			for starty in range(0, self.__h - 14, 13):
				for startx in range(0, self.__w - 62, 64):
					i += 1
					if i == len(Env.HOSTS):
						break
				if i == len(Env.HOSTS):
					break
			if self.__mpp != i:
				self.__mpp = i
				self.__page = 0
			self.__redraw = True

		# Down: next page
		elif key == curses.KEY_DOWN:
			self.__page += 1
			if len(Env.HOSTS) <= self.__mpp * self.__page:
				self.__page -= 1
			else:
				self.__redraw = True

		# Up: previous page
		elif key == curses.KEY_UP:
			if self.__page != 0:
				self.__page -= 1
				self.__redraw = True

		# Left: zoom-out
		elif key == curses.KEY_LEFT:
			self.__timescale += 1
			if self.__timescale > 4:
				self.__timescale -= 1
			else:
				self.__redraw = True

		# Right: zoom-in
		elif key == curses.KEY_RIGHT:
			if self.__timescale != 0:
				self.__timescale -= 1
				self.__redraw = True

		return True
	

	def __elapse(self):
		if self.__timer == 0:
			for m in Env.HOSTS:
				self.__window.addstr(self.__h - 1, 0, "Loading ...                                     ")
				self.__window.refresh()
				try:
					self.__cpu_num[m] = Utils.safeInt(System.__getRRD("%s/%s/cpu_num.rrd" % (Env.DATADIR, m))[-1][1])
					self.__cpu_speed[m] = Utils.safeFloat(System.__getRRD("%s/%s/cpu_speed.rrd" % (Env.DATADIR, m))[-1][1])
					self.__cpu_user[m] = System.__getRRD("%s/%s/cpu_user.rrd" % (Env.DATADIR, m))
					self.__cpu_system[m] = System.__getRRD("%s/%s/cpu_system.rrd" % (Env.DATADIR, m))

					self.__mem_buffers[m] = System.__getRRD("%s/%s/mem_buffers.rrd" % (Env.DATADIR, m))
					self.__mem_cached[m] = System.__getRRD("%s/%s/mem_cached.rrd" % (Env.DATADIR, m))
					self.__mem_free[m] = System.__getRRD("%s/%s/mem_free.rrd" % (Env.DATADIR, m))
					self.__mem_total[m] = System.__getRRD("%s/%s/mem_total.rrd" % (Env.DATADIR, m))

					self.__cpu_topuser[m] = System.__getProcData("%s/%s/cpu_topuser" % (Env.DATADIR, m))
					self.__mem_topuser[m] = System.__getProcData("%s/%s/mem_topuser" % (Env.DATADIR, m))
				except ElementTree.ParseError:
					return False
				except IOError:
					return False

			self.__redraw = True

		# go ahead
		self.__timer += 1
		if self.__timer >= 6000:
			self.__timer -= 6000

		return True
	

	def __drawStatus(self, x, y, current, step, hostname):
		
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

		cpu_title = "cpu (%d * %sHz)" % (cpu_num, (("%.1fG" % (cpu_speed / 1000)) if cpu_speed >= 1000 else ("%.1fM" % cpu_speed)))
		mem_title = "mem (%siB)" % (("%.1fG" % (mem_total[-1][1] / 1024 / 1024)) if mem_total[-1][1] >= 1024 else ("%.1fM" % (mem_total[-1][1] / 1024)))
		self.__window.addstr(y + 1, x, "                                                               ")
		self.__window.addstr(y + 1, x + int((32 - len(cpu_title)) / 2), cpu_title)
		self.__window.addstr(y + 1, x + 31 + int((32 - len(mem_title)) / 2), mem_title)
		self.__window.addstr(y + 2, x, "|------------------------------|------------------------------|")
		self.__window.addstr(y + 3, x, "|                              |##############################|")
		self.__window.addstr(y + 4, x, "|                              |##############################|")
		self.__window.addstr(y + 5, x, "|                              |##############################|")
		self.__window.addstr(y + 6, x, "|                              |##############################|")
		self.__window.addstr(y + 7, x, "|                              |##############################|")
		self.__window.addstr(y + 8, x, "|------------------------------|------------------------------|")
		self.__window.addstr(y + 9, x, "|                              |                              |")
		self.__window.addstr(y +10, x, "|                              |                              |")
		self.__window.addstr(y +11, x, "|------------------------------|------------------------------|")
	
		for j in range(30):
			val1 = System.__getRRDValue(cpu_system, current + (j - 29) * step, step)
			val2 = System.__getRRDValue(cpu_user, current + (j - 29) * step, step)
			if val1 < 0 or val2 < 0:
				self.__window.addstr(y + 3, x + 1 + j, "?")
				self.__window.addstr(y + 4, x + 1 + j, "?")
				self.__window.addstr(y + 5, x + 1 + j, "?")
				self.__window.addstr(y + 6, x + 1 + j, "?")
				self.__window.addstr(y + 7, x + 1 + j, "?")
				continue
			val2 += val1
			if val2 > 0:  self.__window.addstr(y + 7, x + 1 + j, "#")
			if val2 > 20: self.__window.addstr(y + 6, x + 1 + j, "#")
			if val2 > 40: self.__window.addstr(y + 5, x + 1 + j, "#")
			if val2 > 60: self.__window.addstr(y + 4, x + 1 + j, "#")
			if val2 > 80: self.__window.addstr(y + 3, x + 1 + j, "#")
			if val1 > 0:  self.__window.addstr(y + 7, x + 1 + j, "@")
			if val1 > 20: self.__window.addstr(y + 6, x + 1 + j, "@")
			if val1 > 40: self.__window.addstr(y + 5, x + 1 + j, "@")
			if val1 > 60: self.__window.addstr(y + 4, x + 1 + j, "@")
			if val1 > 80: self.__window.addstr(y + 3, x + 1 + j, "@")

		i = 0
		for u in cpu_topuser:
			mu = u[:]
			mu[1] += "%"
			mu[2] = mu[2].split("/")[-1]
			s = " ".join(mu)
			self.__window.addstr(y + 9 + i, x + 2, s[:28])
			i += 1
	
		for j in range(30):
			total = System.__getRRDValue(mem_total, current + (j - 29) * step, step)
			val1 = System.__getRRDValue(mem_free, current + (j - 29) * step, step)
			val2 = System.__getRRDValue(mem_cached, current + (j - 29) * step, step)
			val3 = System.__getRRDValue(mem_buffers, current + (j - 29) * step, step)
			if total < 0 or val1 < 0 or val2 < 0 or val3 < 0:
				self.__window.addstr(y + 3, x + 32 + j, "?")
				self.__window.addstr(y + 4, x + 32 + j, "?")
				self.__window.addstr(y + 5, x + 32 + j, "?")
				self.__window.addstr(y + 6, x + 32 + j, "?")
				self.__window.addstr(y + 7, x + 32 + j, "?")
				continue
			val1 /= total
			val2 = val1 + (val2 + val3) / total
			if val2 >= 0.2: self.__window.addstr(y + 3, x + 32 + j, ".")
			if val2 >= 0.4: self.__window.addstr(y + 4, x + 32 + j, ".")
			if val2 >= 0.6: self.__window.addstr(y + 5, x + 32 + j, ".")
			if val2 >= 0.8: self.__window.addstr(y + 6, x + 32 + j, ".")
			if val2 == 1.0: self.__window.addstr(y + 7, x + 32 + j, ".")
			if val1 >= 0.2: self.__window.addstr(y + 3, x + 32 + j, " ")
			if val1 >= 0.4: self.__window.addstr(y + 4, x + 32 + j, " ")
			if val1 >= 0.6: self.__window.addstr(y + 5, x + 32 + j, " ")
			if val1 >= 0.8: self.__window.addstr(y + 6, x + 32 + j, " ")
			if val1 == 1.0: self.__window.addstr(y + 7, x + 32 + j, " ")
	
		i = 0
		for u in mem_topuser:
			mu = u[:]
			mu[1] += "%"
			mu[2] = mu[2].split("/")[-1]
			s = " ".join(mu)
			self.__window.addstr(y + 9 + i, x + 33, s[:28])
			i += 1
	
		return current - j * step, current

	
	def __draw(self):
		self.__window.erase()
		i = self.__mpp * self.__page
		starttime = 0
		endtime = 0
		now = int(time.mktime(datetime.now().timetuple()))
		now -= now % 60
		for starty in range(0, self.__h - 14, 13):
			for startx in range(0, self.__w - 62, 65):
				hostname = Env.HOSTS[i]

				self.__window.addstr(starty + 0, startx, "                                                               ")
				self.__window.addstr(starty + 0, startx + int((63 - len(hostname)) / 2), hostname)

				if self.__timescale == 0:
					step = 60 # 30 mins
				elif self.__timescale == 1:
					step = 240 # 2 hours
				elif self.__timescale == 2:
					step = 1440 # 12 hours
				elif self.__timescale == 3:
					step = 11520 # 4 days
				else:
					step = 86400 # 30 days

				# each statuses
				starttime, endtime = self.__drawStatus(startx, starty, now, step, hostname)
				
				i += 1
				if i == len(Env.HOSTS):
					break

			if i == len(Env.HOSTS):
				break

		starttimestr = datetime.fromtimestamp(starttime).strftime('%Y-%m-%d %H:%M:%S')
		endtimestr = datetime.fromtimestamp(endtime).strftime('%Y-%m-%d %H:%M:%S')
		self.__window.addstr(starty + 13, 1, "[ # ] user   [ @ ] sys         [ # ] user   [ . ] cache/buff")
		self.__window.addstr(self.__h - 1, 1, "%s - %s" % (starttimestr, endtimestr))

		self.__window.refresh()


	def __mainloop(self):
		while True:
			self.__redraw = False

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
				pass
			
			self.__firstloop = False


	def run(self):
		self.__initial()
		self.__mainloop()
		self.__final()

