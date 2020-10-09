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

redzone_ui_print = Blueprint('redzone_ui', __name__, template_folder='views')

prefix = ""
if os.path.exists("/home/zhecht/fantasy"):
	# if on linux aka prod
	prefix = "/home/zhecht/fantasy/"

curr_week = 4

@redzone_ui_print.route('/redzone')
def redzone_ui_route():
	team_trans = {"rav": "bal", "htx": "hou", "oti": "ten", "sdg": "lac", "ram": "lar", "clt": "ind", "crd": "ari", "gnb": "gb", "kan": "kc", "nwe": "ne", "rai": "lv", "sfo": "sf", "tam": "tb", "nor": "no"}
	rbbc_teams = ['crd', 'atl', 'rav', 'buf', 'car', 'chi', 'cin', 'cle', 'dal', 'den', 'det', 'gnb', 'htx', 'clt', 'jax', 'kan', 'sdg', 'ram', 'rai', 'mia', 'min', 'nor', 'nwe', 'nyg', 'nyj', 'phi', 'pit', 'sea', 'sfo', 'tam', 'oti', 'was']
	
	top_redzone = get_player_looks_arr(curr_week, is_ui=True)
	sorted_looks = sorted(top_redzone, key=operator.itemgetter("looks", "looks_perc"), reverse=True)
	sorted_looks_perc = sorted(top_redzone, key=operator.itemgetter("looks_perc"), reverse=True)

	#feelsbad_players = ["amari cooper", "sammy watkins", "stefon diggs", "adam thielen", "calvin ridley", "michael thomas", "odell beckham", "robert woods", "oj howard", "brandin cooks", "robby anderson"]
	feelsbad = {}
	players_on_teams,translations = read_rosters()
	players_on_FA = read_FA()
	players_on_teams = {**players_on_teams, **players_on_FA}
	update_players_on_teams(players_on_teams)

	table = ""
	header = "<tr><th>Player</th><th>looks/team looks</th><th>Team RZ Look Share</th><th>1 Week Trend</th></tr>"

	table += "<table><tr><th colspan='4'>The Julio Jones Table</th></tr>"
	table += header
	for player in sorted_looks:
		if player["name"] == "julio jones":
			table += f"<tr><td>{player['name'].title()}</td><td>{player['looks']}/{player['total_team_looks']}</td><td>{player['looks_perc']}%</td><td>{player['delta']}</td></tr>"
	table += "</table>"

	pos_data = [("RB", 40), ("WR", 50), ("TE", 30)]
	for pos, cutoff in pos_data:
		table += f"<table><tr><th colspan='4'>Top {cutoff} {pos}</th></tr>"
		table += header
		printed = 0
		for player in sorted_looks:
			if printed == cutoff:
				break
			if player["looks"] >= 0 and players_on_teams[player["name"]]["position"] == pos:
				printed += 1
				table += f"<tr><td>{player['name'].title()}</td><td>{player['looks']}/{player['total_team_looks']}</td><td>{player['looks_perc']}%</td><td>{player['delta']}</td></tr>"
		table += "</table>"

	return render_template("redzone_ui.html", table=table)
