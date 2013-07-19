# -*- coding: utf-8; indent-tabs-mode: t; tab-width: 4 -*-
#
# settings.py
#

import configparser
from ganglist import config


class Options: pass

class Environment: pass

class Settings:

	def __init__(self):

		import os

		self.options = Options()
		self.environment = Environment()
		self.colorMap = {} # {string name: int colorno}

		HOME_DIR = os.environ["HOME"]
		CONF_BASENAME = "ganglist.conf"

		conffile = configparser.ConfigParser()

		if os.path.exists(config.SYSTEM_CONFIG_DIR + "/" + CONF_BASENAME):
			conffile.read(config.SYSTEM_CONFIG_DIR + "/" + CONF_BASENAME)
		if os.path.exists(HOME_DIR + "/." + CONF_BASENAME):
			conffile.read(HOME_DIR + "/." + CONF_BASENAME)

		if "Options" in conffile:
			self.options.DEFAULT_WIDTH = conffile["Options"].getint("DEFAULT_WIDTH", 30)
			self.options.DEFAULT_HEIGHT = conffile["Options"].getint("DEFAULT_HEIGHT", 5)
			self.options.DEFAULT_INTERVAL = conffile["Options"].getint("DEFAULT_INTERVAL", 60)
			self.options.DEFAULT_SHOWUSERS = conffile["Options"].getboolean("DEFAULT_SHOWUSERS", True)
			self.options.DEFAULT_INLINE = conffile["Options"].getboolean("DEFAULT_INLINE", False)
			self.options.DEFAULT_COLORING = conffile["Options"].getboolean("DEFAULT_COLORING", True)
			self.options.MIN_WIDTH = conffile["Options"].getint("MIN_WIDTH", 1)
			self.options.MIN_HEIGHT = conffile["Options"].getint("MIN_HEIGHT", 1)
			self.options.MIN_INTERVAL = conffile["Options"].getint("MIN_INTERVAL", 10)
			self.options.MAX_WIDTH = conffile["Options"].getint("MAX_WIDTH", 100)
			self.options.MAX_HEIGHT = conffile["Options"].getint("MAX_HEIGHT", 100)
			self.options.MAX_INTERVAL = conffile["Options"].getint("MAX_INTERVAL", 600)

		if "Environment" in conffile:
			self.environment.DATADIR = conffile["Environment"].get("DATADIR", config.LOCAL_STATE_DIR + "/log/ganglist")
			self.environment.HOSTS = conffile["Environment"].get("HOSTS", "").split()

		if "Colors" in conffile:
			self.colorMap["USER"] = conffile["Colors"].getint("USER", 1)
			self.colorMap["SYSTEM"] = conffile["Colors"].getint("SYSTEM", 2)
			self.colorMap["CACHE"] = conffile["Colors"].getint("CACHE", 3)
