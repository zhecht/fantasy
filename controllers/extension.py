
from flask import *
from bs4 import BeautifulSoup as BS
from sys import platform

import json
import operator
import os
import re
import urllib

try:
  import controllers.read_rosters as read_rosters
  from controllers.functions import *
except:
  import read_rosters
  from functions import *


extension_blueprint = Blueprint('extension', __name__, template_folder='views')

prefix = ""
if os.path.exists("/home/zhecht/fantasy"):
	prefix = "/home/zhecht/fantasy/"
elif os.path.exists("/home/playerprops/fantasy"):
	# if on linux aka prod
	prefix = "/home/playerprops/fantasy/"
elif os.path.exists("/mnt/c/Users/Zack/Documents/fantasy"):
	prefix = "/mnt/c/Users/Zack/Documents/fantasy/"

def write_cron_trade_values():
	tradevalues = {}
	tier = 1
	for scoring in ["standard", "half", "full"]:
		lines = open(f"{prefix}static/trade_value/tradevalues_{scoring}.csv").readlines()
		for line in lines[4:]:
			allTds = line.split(",")

			# If points column exists
			if len(allTds[2]) > 0:
				value = float(allTds[2])
				for td in allTds[3:]:
					try:
						name = fixName(td.strip()).strip()
						if not name or name == "home":
							continue
						if name not in tradevalues:
							tradevalues[name] = {"standard": 0, "half": 0, "full": 0}
						tradevalues[name][scoring] = value
					except:
						pass

	with open(f"{prefix}static/trade_value/tradevalues.json", "w") as fh:
		json.dump(tradevalues, fh, indent=4)

def read_trade_values():
	with open("{}static/trade_value/tradevalues.json".format(prefix)) as fh:
		returned_json = json.loads(fh.read())
	return returned_json

def write_borischen_extension():

	stats = {}
	positions = ["quarterback", "half-05-5-ppr-running-back", "half-05-5-ppr-wide-receiver", "half-05-5-ppr-tight-end", "kicker", "defense-dst"]
	#player_ids = yahoo_stats.read_yahoo_ids()

	for pos in positions:
		if pos.find("wide") == -1:
			html = urllib.urlopen("http://www.borischen.co/p/{}-tier-rankings.html".format(pos))
		else:
			html = urllib.urlopen("http://www.borischen.co/p/{}-tier.html".format(pos))
		soup = BS(html.read(), "lxml")
		aws_link = soup.find("object").get("data")

		html = urllib.urlopen(aws_link)
		soup = BS(html.read(), "lxml")

		tiers = soup.find("p").text.split("\n")[:-1]
		for tier in tiers:
			m = re.search(r"Tier ([0-9]+): (.*)", tier)
			tier = int(m.group(1))
			players = m.group(2).split(", ")
			
			for name in players:
				try:
					if pos.find("defense") == -1:
						stats[player_ids[fixName(name.lower().replace("'", ""))]] = tier
					else:
						stats[player_ids[' '.join(name.lower().split())[:-1]]] = tier
				except:
					#print(name)
					pass
				#stats[name.lower()] = tier
	return
	with open("static/borischen_tiers.json", "w") as fh:
		json.dump(stats, fh, indent=4)

#write_borischen_extension()

def read_borischen_extension(host):
	with open("static/borischen_tiers.json") as fh:
		returned_json = json.loads(fh.read())
	return returned_json


@extension_blueprint.route('/extension')
def extension_route():

	if request.args.get("borischen"):
		return jsonify(tiers=read_borischen_extension(request.args.get("host")))

	try:
		total_teams = int(request.args.get("total_teams"))
	except:
		total_teams = 2
	is_espn = request.args.get("is_espn") == "true"
	is_nfl = request.args.get("is_nfl") == "true"
	is_yahoo = request.args.get("is_yahoo") == "true"
	try:
		is_sleeper = request.args.get("is_sleeper") == "true"
		is_cbs = request.args.get("is_cbs") == "true"
	except:
		is_sleeper = False
		is_cbs = False
	rosters, translations = read_rosters.read_rosters()
	trade_values = read_trade_values()
	results_arr = []

	for team_idx in range(total_teams):
		player_len = int(request.args.get(f"team_{team_idx}_len"))

		for player_idx in range(player_len):
			player = request.args.get(f"team_{team_idx}_player_{player_idx}")
			try:
				name,team,pos,clicked = player.split(",")
			except:
				continue
			full_name = fixName(name)
			
			if is_sleeper:
				try:
					if len(name.split(" ")[0]) == 2 and name.split(" ")[0][-1] == '.':
						# if shortened name
						full_name = translations[name+" "+team]
					else:
						full_name = fixName(full_name.replace("'", "").replace("/", ""))
				except:
					continue
			elif not is_cbs and not is_nfl and not is_espn and pos != "DEF" and request.args.get("evaluate") == "false":
				try:
					full_name = translations[name+" "+team]
				except:
					continue
			elif is_cbs or is_espn or is_nfl or is_yahoo:
				full_name = fixName(full_name.replace("'", "").replace("/", ""))

			try:
				vals = [ str(trade_values[fixName(full_name)][s]) for s in ["standard", "half", "full"] ]
			except:
				vals = ["0","0","0"]

			results_arr.append({"team": team_idx, "full": fixName(full_name).title(), "full_val": float(vals[-1]),"vals": vals, "clicked": clicked})
	
	results_arr = sorted(results_arr, key=operator.itemgetter("full_val"), reverse=True)
	results = {}
	for i in range(total_teams):
		results[f"team{i}"] = []

	for res in results_arr:
		team = res["team"]
		values = f"{res['full']},{'_'.join(res['vals'])},{res['clicked']}"
		results[f"team{team}"].append(values)

	updated = open(f"{prefix}static/trade_value/updated").read()
	return jsonify(teams=results, team0=results["team0"], team1=results["team1"], updated=updated, total_teams=total_teams)

if __name__ == '__main__':
	write_cron_trade_values()
