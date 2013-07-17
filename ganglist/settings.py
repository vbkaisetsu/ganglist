# -*- coding: utf-8; indent-tabs-mode: t; tab-width: 4 -*-
#
# settings.py
#

import configparser
from ganglist import config


class Options:

	def __init__(self):
		# default values for command-line options
		self.DEFAULT_WIDTH = 30
		self.DEFAULT_HEIGHT = 5
		self.DEFAULT_INTERVAL = 60
		self.DEFAULT_SHOWUSERS = True
		self.DEFAULT_INLINE = False
		self.DEFAULT_COLORING = False

		# minimum values for command-line options
		self.MIN_WIDTH = 1
		self.MIN_HEIGHT = 1
		self.MIN_INTERVAL = 10

		# maximum values for command-line options
		self.MAX_WIDTH = 100
		self.MAX_HEIGHT = 100
		self.MAX_INTERVAL = 600


class Environment:

	def __init__(self):
		# data directory
		self.DATADIR = config.LOCAL_STATE_DIR + "/log/ganglist"

		# host list
		self.HOSTS = []


class Settings:

	def __init__(self):
	
		import os

		self.options = Options()
		self.environment = Environment()

		HOME_DIR = os.environ["HOME"]		
		CONF_BASENAME = "ganglist.conf"
		
		conffile = configparser.ConfigParser()
		
		if os.path.exists(config.SYSTEM_CONFIG_DIR + "/" + CONF_BASENAME):
			conffile.read(config.SYSTEM_CONFIG_DIR)
		if os.path.exists(HOME_DIR + "/." + CONF_BASENAME):
			conffile.read(HOME_DIR + "/." + CONF_BASENAME)

		if "Environment" in conffile:
			if "DEFAULT_WIDTH" in conffile["Options"]:
				self.options.DEFAULT_WIDTH = conffile["Options"].getint("DEFAULT_WIDTH")
			if "DEFAULT_HEIGHT" in conffile["Options"]:
				self.options.DEFAULT_HEIGHT = conffile["Options"].getint("DEFAULT_HEIGHT")
			if "DEFAULT_INTERVAL" in conffile["Options"]:
				self.options.DEFAULT_INTERVAL = conffile["Options"].getint("DEFAULT_INTERVAL")
			if "DEFAULT_SHOWUSERS" in conffile["Options"]:
				self.options.DEFAULT_SHOWUSERS = conffile["Options"].getboolean("DEFAULT_SHOWUSERS")
			if "DEFAULT_INLINE" in conffile["Options"]:
				self.options.DEFAULT_INLINE = conffile["Options"].getboolean("DEFAULT_INLINE")
			if "MIN_WIDTH" in conffile["Options"]:
				self.options.MIN_WIDTH = conffile["Options"].getint("MIN_WIDTH")
			if "MIN_HEIGHT" in conffile["Options"]:
				self.options.MIN_HEIGHT = conffile["Options"].getint("MIN_HEIGHT")
			if "MIN_INTERVAL" in conffile["Options"]:
				self.options.MIN_INTERVAL = conffile["Options"].getint("MIN_INTERVAL")
			if "MAX_WIDTH" in conffile["Options"]:
				self.options.MAX_WIDTH = conffile["Options"].getint("MAX_WIDTH")
			if "MAX_HEIGHT" in conffile["Options"]:
				self.options.MAX_HEIGHT = conffile["Options"].getint("MAX_HEIGHT")
			if "MAX_INTERVAL" in conffile["Options"]:
				self.options.MAX_INTERVAL = conffile["Options"].getint("MAX_INTERVAL")

		if "Environment" in conffile:
			if "DATADIR" in conffile["Environment"]:
				self.environment.DATADIR = conffile["Environment"]["DATADIR"]
			if "HOSTS" in conffile["Environment"]:
				self.environment.HOSTS = conffile["Environment"]["HOSTS"].split()

