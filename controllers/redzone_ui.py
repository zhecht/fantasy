#from selenium import webdriver
from flask import *
from subprocess import call
from bs4 import BeautifulSoup as BS
from sys import platform
from datetime import datetime

import json
import math
import operator
import os
import subprocess
import re

from controllers.redzone import *
from controllers.functions import *

redzone_ui_print = Blueprint('redzone_ui', __name__, template_folder='views')

prefix = ""
if os.path.exists("/home/zhecht/fantasy"):
	# if on linux aka prod
	prefix = "/home/zhecht/fantasy/"

team_trans = {"rav": "bal", "htx": "hou", "oti": "ten", "sdg": "lac", "ram": "lar", "clt": "ind", "crd": "ari", "gnb": "gb", "kan": "kc", "nwe": "ne", "rai": "lv", "sfo": "sf", "tam": "tb", "nor": "no"}

@redzone_ui_print.route("/getRedzone")
def getRedzone():
	redzoneResult = []
	top_redzone = get_player_looks_arr(curr_week, is_ui=True)
	sorted_looks = sorted(top_redzone, key=operator.itemgetter("looks_per_game"), reverse=True)
	sorted_looks_perc = sorted(top_redzone, key=operator.itemgetter("looks_perc"), reverse=True)
	players_on_teams,translations = read_rosters()
	players_on_FA = read_FA()
	players_on_teams = {**players_on_teams, **players_on_FA}
	update_players_on_teams(players_on_teams)
	counts = {}
	for playerData in sorted_looks:
		player = playerData["name"]
		team = playerData["team"]
		team_display = team_trans[team] if team in team_trans else team

		pos = players_on_teams[player]["position"]
		if pos not in counts:
			counts[pos] = 0
		elif pos == "TE" and counts[pos] >= 40:
			continue
		elif counts[pos] >= 50:
			continue
		counts[pos] += 1
		
		redzoneResult.append({
			"position": pos,
			"player": player.title(),
			"team": team_display.upper(),
			"looksPerc": playerData["looks_perc"],
			"looksPerGame": playerData["looks_per_game"],
			"delta": playerData["delta"],
			"delta3": playerData["delta3"],
		})

	return jsonify(redzoneResult)

@redzone_ui_print.route('/redzone')
def redzone_ui_route():
	return render_template("redzone_ui.html")
