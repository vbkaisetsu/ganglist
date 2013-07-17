# -*- coding: utf-8; indent-tabs-mode: t; tab-width: 4 -*-
# 
# screen.py
# 

import curses
from gettext import gettext as _


# wrapper of curses
class Screen:


	# key mapping
	__KEYMAP = {
		curses.KEY_RESIZE: 'RESIZE',
		curses.KEY_UP: 'UP',
		curses.KEY_DOWN: 'DOWN',
		curses.KEY_LEFT: 'LEFT',
		curses.KEY_RIGHT: 'RIGHT'}

	# timeout interval
	__TIMEOUT = 10
	
	# Singleton object
	__obj = None


	@staticmethod
	def timeout():
		return Screen.__TIMEOUT


	def __init__(self, coloring):
		# check and set singleton object
		if Screen.__obj is not None:
			raise RuntimeError(_('Duplicate "Screen" object.'))
		Screen.__obj = self

		# initialize
		self.__scr = curses.initscr()
		curses.noecho()
		curses.cbreak()
		curses.raw()
		self.__scr.keypad(1)
		self.__scr.timeout(Screen.__TIMEOUT)

		# for self.__h, self.__w
		self.__updateSize()

		# settings
		self.__coloring = coloring and curses.has_colors()

		# color settings
		if self.__coloring:
			curses.start_color()
			curses.init_pair(1, 1, 1)
			curses.init_pair(2, 2, 2)
			curses.init_pair(3, 3, 3)

	
	# Users MUST call this method when they finish using this class
	def final(self):
		# finalize
		self.__scr.keypad(0)
		curses.noraw()
		curses.nocbreak()
		curses.echo()
		curses.endwin()

		# unset singleton object
		__obj = None


	def __updateSize(self):
		self.__h, self.__w = self.__scr.getmaxyx()


	def getch(self):
		key = self.__scr.getch()

		# update screen size data
		if key == curses.KEY_RESIZE:
			self.__updateSize()

		if key in Screen.__KEYMAP:
			return Screen.__KEYMAP[key]
		return key


	def erase(self):
		self.__scr.erase()


	def width(self):
		return self.__w


	def height(self):
		return self.__h


	# NOTE:
	# when resizing occured with drawing the screen,
	# curses throws a exception.
	# since the screen will be refreshed when receiving next KEY_RESIZE message,
	# this exception may be ignored.


	def refresh(self):
		try:
			self.__scr.move(self.__h - 1, 0)
			self.__scr.refresh()
		except curses.error:
			pass


	def write(self, y, x, text, colorno=0):
		try:
			if (self.__coloring):
				self.__scr.attrset(curses.color_pair(colorno))
			self.__scr.addstr(y, x, text)
		except curses.error:
			pass


	def writeFooter(self, text):
		try:
			if (self.__coloring):
				self.__scr.attrset(curses.color_pair(0))
			self.__scr.addstr(self.__h - 1, 0, ' ' * (self.__w - 1))
			self.__scr.addstr(self.__h - 1, 1, text)
		except curses.error:
			pass

