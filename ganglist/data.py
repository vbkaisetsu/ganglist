# -*- coding: utf-8; indent-tabs-mode: t; tab-width: 4 -*-
# 
# data.py
# 


from xml.etree import ElementTree
from urllib.request import urlopen

from ganglist.utils import Utils


class Data:
	

	@staticmethod
	def getProcData(filename):
		if "://" in filename:
			fp = urlopen(filename).read().decode("utf-8").strip().split("\n")
		else:
			fp = open(filename, "r")
		lst = []
		for l in fp:
			spl = l.split()
			if len(spl) == 3 and spl[2]:
				spl[2] = spl[2].split("/")[-1]
				lst.append(spl)
		return lst


	# parse xml files dumped from rrds
	@staticmethod
	def getRRD(filename):
		if "://" in filename:
			tree = ElementTree.parse(urlopen(filename))
		else:
			tree = ElementTree.parse(filename)
		elem = tree.getroot()
		rootstep = int(elem.find(".//step").text)
		lastupdate = int(elem.find(".//lastupdate").text)
		dataset = {}
		for e in elem.findall(".//rra"):
			step = int(e.find(".//pdp_per_row").text) * rootstep
			dataset.update({
				lastupdate - i * step: Utils.safeFloat(val.text)
				for i, val in enumerate(reversed(e.findall(".//v")))})
		return sorted(dataset.items(), key=lambda x: x[0])


	@staticmethod
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

