
from sys import platform

import os
import json

try:
	import controllers.defense as defense
except:
	import defense

prefix = ""
if platform != "darwin":
	# if on linux aka prod
	prefix = "/home/zhecht/fantasy/"

files = os.listdir("{}views".format(prefix))
for file in files:
	if file.startswith("click_html_"):
		settings = defense.init_settings(file)
		ranks_html, teams = defense.get_ranks_html(settings)
		click_html = defense.get_team_html(teams, settings)
		with open("{}views/{}".format(prefix, file), "w") as fh:
			fh.write(click_html)