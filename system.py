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


def getprocdata(filename):
	fp = open(filename, "r")
	lst = []
	for l in fp:
		spl = l.split()
		spl[2] = spl[2].split("/")[-1]
		lst.append(spl)
	return lst


# parse xml files dumped from rrds
def getRRD(filename):
	tree = ElementTree.parse(filename)
	elem = tree.getroot()
	rootstep = int(elem.find(".//step").text)
	lastupdate = int(elem.find(".//lastupdate").text)
	dataset = {}
	for e in elem.findall(".//rra"):
		step = int(e.find(".//pdp_per_row").text) * rootstep
		dataset.update({lastupdate - i * step: Utils.safeFloat(val.text) for i, val in enumerate(reversed(e.findall(".//v")))})
	return sorted(dataset.items(), key=lambda x: x[0])


def getRRDValue(data, time, period):
	valsum = 0
	cnt = 0
	for i in range(len(data)):
		if time - period <= data[i][0]:
			cnt += 1
			valsum += data[i][1]
			if time <= data[i][0]:
				return valsum / cnt
	return data[-1][1]


def drawstatus(window, x, y, current, step, cpu_user, cpu_system, cpu_num, cpu_speed, cpu_topuser, mem_free, mem_buffers, mem_cached, mem_total, mem_topuser):
	cputitle = "cpu (%d * %sHz)" % (cpu_num, (("%.1fG" % (cpu_speed / 1000)) if cpu_speed >= 1000 else ("%.1fM" % cpu_speed)))
	memtitle = "mem (%siB)" % (("%.1fG" % (mem_total[-1][1] / 1024 / 1024)) if mem_total[-1][1] >= 1024 else ("%.1fM" % (mem_total[-1][1] / 1024)))
	window.addstr(y + 1, x, "                                                               ")
	window.addstr(y + 1, x + int((32 - len(cputitle)) / 2), cputitle)
	window.addstr(y + 1, x + 31 + int((32 - len(memtitle)) / 2), memtitle)
	window.addstr(y + 2, x, "|------------------------------|------------------------------|")
	window.addstr(y + 3, x, "|                              |##############################|")
	window.addstr(y + 4, x, "|                              |##############################|")
	window.addstr(y + 5, x, "|                              |##############################|")
	window.addstr(y + 6, x, "|                              |##############################|")
	window.addstr(y + 7, x, "|                              |##############################|")
	window.addstr(y + 8, x, "|------------------------------|------------------------------|")
	window.addstr(y + 9, x, "|                              |                              |")
	window.addstr(y +10, x, "|                              |                              |")
	window.addstr(y +11, x, "|------------------------------|------------------------------|")

	for j in range(30):
		val1 = getRRDValue(cpu_system, current + (j - 29) * step, step)
		val2 = getRRDValue(cpu_user, current + (j - 29) * step, step)
		if val1 < 0 or val2 < 0:
			window.addstr(y + 3, x + 1 + j, "?")
			window.addstr(y + 4, x + 1 + j, "?")
			window.addstr(y + 5, x + 1 + j, "?")
			window.addstr(y + 6, x + 1 + j, "?")
			window.addstr(y + 7, x + 1 + j, "?")
			continue
		val2 += val1
		if val2 > 0:  window.addstr(y + 7, x + 1 + j, "#")
		if val2 > 20: window.addstr(y + 6, x + 1 + j, "#")
		if val2 > 40: window.addstr(y + 5, x + 1 + j, "#")
		if val2 > 60: window.addstr(y + 4, x + 1 + j, "#")
		if val2 > 80: window.addstr(y + 3, x + 1 + j, "#")
		if val1 > 0:  window.addstr(y + 7, x + 1 + j, "@")
		if val1 > 20: window.addstr(y + 6, x + 1 + j, "@")
		if val1 > 40: window.addstr(y + 5, x + 1 + j, "@")
		if val1 > 60: window.addstr(y + 4, x + 1 + j, "@")
		if val1 > 80: window.addstr(y + 3, x + 1 + j, "@")

	i = 0
	for u in cpu_topuser:
		mu = u[:]
		mu[1] += "%"
		mu[2] = mu[2].split("/")[-1]
		s = " ".join(mu)
		window.addstr(y + 9 + i, x + 2, s[:28])
		i += 1

	for j in range(30):
		total = getRRDValue(mem_total, current + (j - 29) * step, step)
		val1 = getRRDValue(mem_free, current + (j - 29) * step, step)
		val2 = getRRDValue(mem_cached, current + (j - 29) * step, step)
		val3 = getRRDValue(mem_buffers, current + (j - 29) * step, step)
		if total < 0 or val1 < 0 or val2 < 0 or val3 < 0:
			window.addstr(y + 3, x + 32 + j, "?")
			window.addstr(y + 4, x + 32 + j, "?")
			window.addstr(y + 5, x + 32 + j, "?")
			window.addstr(y + 6, x + 32 + j, "?")
			window.addstr(y + 7, x + 32 + j, "?")
			continue
		val1 /= total
		val2 = val1 + (val2 + val3) / total
		if val2 >= 0.2: window.addstr(y + 3, x + 32 + j, ".")
		if val2 >= 0.4: window.addstr(y + 4, x + 32 + j, ".")
		if val2 >= 0.6: window.addstr(y + 5, x + 32 + j, ".")
		if val2 >= 0.8: window.addstr(y + 6, x + 32 + j, ".")
		if val2 == 1.0: window.addstr(y + 7, x + 32 + j, ".")
		if val1 >= 0.2: window.addstr(y + 3, x + 32 + j, " ")
		if val1 >= 0.4: window.addstr(y + 4, x + 32 + j, " ")
		if val1 >= 0.6: window.addstr(y + 5, x + 32 + j, " ")
		if val1 >= 0.8: window.addstr(y + 6, x + 32 + j, " ")
		if val1 == 1.0: window.addstr(y + 7, x + 32 + j, " ")

	i = 0
	for u in mem_topuser:
		mu = u[:]
		mu[1] += "%"
		mu[2] = mu[2].split("/")[-1]
		s = " ".join(mu)
		window.addstr(y + 9 + i, x + 33, s[:28])
		i += 1

	return current - j * step, current


def run(window):
	timescale = 0
	timer = 0

	window.timeout(10)

	mpp = 0

	page = 0
	firstloop = True

	cpu_num = {}
	cpu_speed = {}
	cpu_user = {}
	cpu_system = {}

	mem_buffers = {}
	mem_cached = {}
	mem_free = {}
	mem_total = {}

	cpu_topuser = {}
	mem_topuser = {}

	while(True):

		redraw = False

		pressedkey = window.getch();
		# Q: Quit
		if pressedkey == ord("q"):
			return
		# Resize
		elif pressedkey == curses.KEY_RESIZE or firstloop:
			# get machines per page
			i = 0
			h, w = window.getmaxyx()
			if h < 15 or w < 63:
				return
			for starty in range(0, h - 14, 13):
				for startx in range(0, w - 62, 64):
					i += 1
					if i == len(Env.HOSTS):
						break
				if i == len(Env.HOSTS):
					break
			if mpp != i:
				mpp = i
				page = 0
			redraw = True
		# Down: next page
		elif pressedkey == curses.KEY_DOWN:
			page += 1
			if len(Env.HOSTS) <= mpp * page:
				page -= 1
			else:
				redraw = True
		# Up: previous page
		elif pressedkey == curses.KEY_UP:
			if page != 0:
				page -= 1
				redraw = True
		# Left: zoom-out
		elif pressedkey == curses.KEY_LEFT:
			timescale += 1
			if timescale > 4:
				timescale -= 1
			else:
				redraw = True
		# Right: zoom-in
		elif pressedkey == curses.KEY_RIGHT:
			if timescale != 0:
				timescale -= 1
				redraw = True
		# Update
		if timer == 0:
			for m in Env.HOSTS:
				window.addstr(h - 1, 0, "Loading ...                                     ")
				window.refresh()
				try:
					cpu_num[m] = Utils.safeInt(getRRD("%s/%s/cpu_num.rrd" % (Env.DATADIR, m))[-1][1])
					cpu_speed[m] = Utils.safeFloat(getRRD("%s/%s/cpu_speed.rrd" % (Env.DATADIR, m))[-1][1])
					cpu_user[m] = getRRD("%s/%s/cpu_user.rrd" % (Env.DATADIR, m))
					cpu_system[m] = getRRD("%s/%s/cpu_system.rrd" % (Env.DATADIR, m))

					mem_buffers[m] = getRRD("%s/%s/mem_buffers.rrd" % (Env.DATADIR, m))
					mem_cached[m] = getRRD("%s/%s/mem_cached.rrd" % (Env.DATADIR, m))
					mem_free[m] = getRRD("%s/%s/mem_free.rrd" % (Env.DATADIR, m))
					mem_total[m] = getRRD("%s/%s/mem_total.rrd" % (Env.DATADIR, m))

					cpu_topuser[m] = getprocdata("%s/%s/cpu_topuser" % (Env.DATADIR, m))
					mem_topuser[m] = getprocdata("%s/%s/mem_topuser" % (Env.DATADIR, m))

				except ElementTree.ParseError as e:
					return

				except IOError as e:
					return

			redraw = True

		if redraw:
			window.erase()
			i = mpp * page
			starttime = 0
			endtime = 0
			now = int(time.mktime(datetime.now().timetuple()))
			now = now - now % 60
			for starty in range(0, h - 14, 13):
				for startx in range(0, w - 62, 65):
					window.addstr(starty + 0, startx, "                                                               ")
					window.addstr(starty + 0, startx + int((63 - len(Env.HOSTS[i])) / 2), Env.HOSTS[i])

					if timescale == 0:
						step = 60 # 30 mins
					elif timescale == 1:
						step = 240 # 2 hours
					elif timescale == 2:
						step = 1440 # 12 hours
					elif timescale == 3:
						step = 11520 # 4 days
					else:
						step = 86400 # 30 days

					starttime, endtime = drawstatus(window, startx, starty, now, step,
						                        cpu_user[Env.HOSTS[i]], cpu_system[Env.HOSTS[i]], cpu_num[Env.HOSTS[i]], cpu_speed[Env.HOSTS[i]], cpu_topuser[Env.HOSTS[i]],
						                        mem_free[Env.HOSTS[i]], mem_buffers[Env.HOSTS[i]], mem_cached[Env.HOSTS[i]], mem_total[Env.HOSTS[i]], mem_topuser[Env.HOSTS[i]])
					i += 1
					if i == len(Env.HOSTS):
						break

				if i == len(Env.HOSTS):
					break

			starttimestr = datetime.fromtimestamp(starttime).strftime('%Y-%m-%d %H:%M:%S')
			endtimestr = datetime.fromtimestamp(endtime).strftime('%Y-%m-%d %H:%M:%S')
			window.addstr(starty + 13, 1, "[ # ] user   [ @ ] sys         [ # ] user   [ . ] cache/buff")
			window.addstr(h - 1, 1, "%s - %s" % (starttimestr, endtimestr))

			window.refresh()

		timer += 1
		if timer > 6000:
			timer = 0

		firstloop = False


def main(options):
	window = curses.initscr()
	curses.noecho()
	curses.cbreak()
	window.keypad(1)
	run(window)
	curses.nocbreak()
	window.keypad(0)
	curses.echo()
	curses.endwin()

