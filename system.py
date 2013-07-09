#!/usr/bin/python3
# -*- coding: utf-8; indent-tabs-mode: t; tab-width: 4 -*-
#
#  Copyright (C) Koichi Akabe 2013 <vbkaisetsu@gmail.com>
# 
#  ganglist is free software: you can redistribute it and/or modify it
#  under the terms of the GNU General Public License as published by the
#  Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
# 
#  ganglist is distributed in the hope that it will be useful, but
#  WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#  See the GNU General Public License for more details.
# 
#  You should have received a copy of the GNU General Public License along
#  with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import curses
import datetime
from xml.etree import ElementTree

DATADIR = "/project/nakamura-lab01/ganglist"

machines = [
	"ahcclust01.naist.jp", "ahcclust02.naist.jp", "ahcclust03.naist.jp",
	"ahcclust04.naist.jp", "ahcclust05.naist.jp", "ahcclust06.naist.jp",
	"ahcclust07.naist.jp", "ahcclust08.naist.jp", "ahcclust09.naist.jp",
	"ahcclust10.naist.jp", "ahcclust11.naist.jp", "ahcclust12.naist.jp",
]

def getprocdata(filename):
	fp = open(filename, "r")
	lst = []
	for l in fp:
		spl = l.split()
		spl[2] = spl[2].split("/")[-1]
		lst.append(spl)
	return lst

def safe_int(val):
	try:
		return int(val)
	except ValueError:
		return -1

def safe_float(val):
        try:
                return float(val)
        except ValueError:
                return -1

# parse xml files dumped from rrds
def getrrd(filename, n):
	tree = ElementTree.parse(filename)
	elem = tree.getroot()
	rootstep = int(elem.find(".//step").text)
	lastupdate = int(elem.find(".//lastupdate").text)
	dataset = []
	for e in elem.findall(".//rra"):
		step = int(e.find(".//pdp_per_row").text) * rootstep
		# TODO: it's bad coding
		# calcurate with different step data 
		if step <= 10:
			if 10 % step != 0:
				dataset.append((0, 0, []))
				continue
			normstep = 10
		elif step <= 240:
			if 240 % step != 0:
				dataset.append((0, 0, []))
				continue
			normstep = 240
		elif step <= 1680:
			if 1680 % step != 0:
				dataset.append((0, 0, []))
				continue
			normstep = 1680
		elif step <= 6720:
			if 6720 % step != 0:
				dataset.append((0, 0, []))
				continue
			normstep = 6720
		elif step <= 57600:
			if 57600 % step != 0:
				dataset.append((0, 0, []))
				continue
			normstep = 57600
		else:
			dataset.append((0, 0, []))
			continue
		timeend = lastupdate - lastupdate % normstep
		timestart = timeend - normstep * (n - 1)
		vals = []
		stepsum = 0
		valsum = 0
		for val in reversed(e.findall(".//v")):
			tmp = safe_float(val.text)
			if valsum == -1 or tmp == -1:
				valsum = -1
			else:
				valsum += tmp
			stepsum += step
			if stepsum >= normstep:
				vals.append(valsum / stepsum * step)
				stepsum = 0
				valsum = 0
			if len(vals) == n:
				break
		vals.reverse()
		dataset.append((timestart, timeend, vals))
	return dataset

# when data is broken
def drawstatus_broken(window, x, y):
	window.addstr(y + 1, x, "                                                               ")
	window.addstr(y + 2, x, "|――――――――――――――――――――――――――――――|――――――――――――――――――――――――――――――|")
	window.addstr(y + 3, x, "|                              |                              |")
	window.addstr(y + 4, x, "|                              |                              |")
	window.addstr(y + 5, x, "|         unavailable          |         unavailable          |")
	window.addstr(y + 6, x, "|                              |                              |")
	window.addstr(y + 7, x, "|                              |                              |")
	window.addstr(y + 8, x, "|――――――――――――――――――――――――――――――|――――――――――――――――――――――――――――――|")
	window.addstr(y + 9, x, "|                              |                              |")
	window.addstr(y +10, x, "|                              |                              |")
	window.addstr(y +11, x, "|――――――――――――――――――――――――――――――|――――――――――――――――――――――――――――――|")


def drawstatus(window, x, y, cpu_user, cpu_system, cpu_num, cpu_speed, cpu_topuser, mem_free, mem_buffers, mem_cached, mem_total, mem_topuser):
	cputitle = "cpu (%d * %sHz)" % (cpu_num, (("%.1fG" % (cpu_speed / 1000)) if cpu_speed >= 1000 else ("%.1fM" % cpu_speed)))
	memtitle = "mem (%siB)" % (("%.1fG" % (mem_total[-1] / 1024 / 1024)) if mem_total[-1] >= 1024 else ("%.1fM" % (mem_total[-1] / 1024)))
	window.addstr(y + 1, x, "                                                               ")
	window.addstr(y + 1, x + int((32 - len(cputitle)) / 2), cputitle)
	window.addstr(y + 1, x + 31 + int((32 - len(memtitle)) / 2), memtitle)
	window.addstr(y + 2, x, "|――――――――――――――――――――――――――――――|――――――――――――――――――――――――――――――|")
	window.addstr(y + 3, x, "|                              |##############################|")
	window.addstr(y + 4, x, "|                              |##############################|")
	window.addstr(y + 5, x, "|                              |##############################|")
	window.addstr(y + 6, x, "|                              |##############################|")
	window.addstr(y + 7, x, "|                              |##############################|")
	window.addstr(y + 8, x, "|――――――――――――――――――――――――――――――|――――――――――――――――――――――――――――――|")
	window.addstr(y + 9, x, "|                              |                              |")
	window.addstr(y +10, x, "|                              |                              |")
	window.addstr(y +11, x, "|――――――――――――――――――――――――――――――|――――――――――――――――――――――――――――――|")

	for j in range(30):
		val1 = cpu_system[j]
		val2 = cpu_user[j]
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
		total = mem_total[j]
		val1 = mem_free[j]
		val2 = mem_cached[j]
		val3 = mem_buffers[j]
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

def main(window):
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
					if i == len(machines):
						break
				if i == len(machines):
					break
			if mpp != i:
				mpp = i
				page = 0
			redraw = True
		# Down: next page
		elif pressedkey == curses.KEY_DOWN:
			page += 1
			if len(machines) <= mpp * page:
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
			for m in machines:
				window.addstr(h - 1, 0, "Loading ...                                     ")
				window.refresh()
				try:
					cpu_num[m] = getrrd("%s/%s/cpu_num.rrd" % (DATADIR, m), 1)
					cpu_speed[m] = getrrd("%s/%s/cpu_speed.rrd" % (DATADIR, m), 1)
					cpu_user[m] = getrrd("%s/%s/cpu_user.rrd" % (DATADIR, m), 30)
					cpu_system[m] = getrrd("%s/%s/cpu_system.rrd" % (DATADIR, m), 30)

					mem_buffers[m] = getrrd("%s/%s/mem_buffers.rrd" % (DATADIR, m), 30)
					mem_cached[m] = getrrd("%s/%s/mem_cached.rrd" % (DATADIR, m), 30)
					mem_free[m] = getrrd("%s/%s/mem_free.rrd" % (DATADIR, m), 30)
					mem_total[m] = getrrd("%s/%s/mem_total.rrd" % (DATADIR, m), 30)

					cpu_topuser[m] = getprocdata("%s/%s/cpu_topuser" % (DATADIR, m))
					mem_topuser[m] = getprocdata("%s/%s/mem_topuser" % (DATADIR, m))

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
			for starty in range(0, h - 14, 13):
				for startx in range(0, w - 62, 65):
					window.addstr(starty + 0, startx, "                                                               ")
					window.addstr(starty + 0, startx + int((63 - len(machines[i])) / 2), machines[i])

					if (cpu_user[machines[i]][timescale][1] == cpu_user[machines[i]][timescale][1] == cpu_num[machines[i]][timescale][1] == cpu_speed[machines[i]][timescale][1] ==
					    mem_free[machines[i]][timescale][1] == mem_buffers[machines[i]][timescale][1] == mem_cached[machines[i]][timescale][1] == mem_total[machines[i]][timescale][1]):
						drawstatus(window, startx, starty,
						           cpu_user[machines[i]][timescale][2], cpu_system[machines[i]][timescale][2], safe_int(cpu_num[machines[i]][timescale][2][0]), cpu_speed[machines[i]][timescale][2][0], cpu_topuser[machines[i]],
						           mem_free[machines[i]][timescale][2], mem_buffers[machines[i]][timescale][2], mem_cached[machines[i]][timescale][2], mem_total[machines[i]][timescale][2], mem_topuser[machines[i]])
						starttime = cpu_user[machines[i]][timescale][0]
						endtime = cpu_user[machines[i]][timescale][1]
					else:
						drawstatus_broken(window, startx, starty)
					i += 1
					if i == len(machines):
						break

				if i == len(machines):
					break
			
			starttimestr = datetime.datetime.fromtimestamp(starttime).strftime('%Y-%m-%d %H:%M:%S')
			endtimestr = datetime.datetime.fromtimestamp(endtime).strftime('%Y-%m-%d %H:%M:%S')
			window.addstr(starty + 13, 1, "[ # ] user   [ @ ] sys         [ # ] user   [ . ] cache/buff")
			window.addstr(h - 1, 1, "%s - %s" % (starttimestr, endtimestr))

			window.refresh()
		
		timer += 1
		if timer > 6000:
			timer = 0
			
		firstloop = False

if __name__ == "__main__":
	window = curses.initscr()
	curses.noecho()
	curses.cbreak()
	window.keypad(1)
	main(window)
	curses.nocbreak()
	window.keypad(0)
	curses.echo()
	curses.endwin()
