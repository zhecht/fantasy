
from flask import *
from bs4 import BeautifulSoup as BS

import json
import operator
import re
import urllib

try:
  import controllers.read_rosters as read_rosters
  import controllers.stats as yahoo_stats
except:
  import read_rosters
  import stats as yahoo_stats


extension = Blueprint('extension', __name__, template_folder='views')

def fix_name(name):
	if name.find("(") != -1:
		name = name.split(" ")[0]
	elif name == "todd gurley":
		return "todd gurley ii"
	elif name == "melvin gordon":
		return "melvin gordon iii"
	elif name == "mitch trubisky":
		return "mitchell trubisky"
	elif name == "willie snead":
		return "willie snead iv"
	elif name == "allen robinson":
		return "allen robinson ii"
	elif name == "ted ginn":
		return "ted ginn jr."
	elif name == "marvin jones":
		return "marvin jones jr."
	elif name == "will fuller":
		return "will fuller v"
	elif name == "paul richardson":
		return "paul richardson jr."
	elif name == "duke johnson":
		return "duke johnson jr."
	elif name == "odell beckham":
		return "odell beckham jr."
	elif name == "mark ingram ii":
		return "mark ingram"
	return name
	
def write_cron_trade_values():
	# Save Standard page as trade_value0.csv
	# Save HALF-PPR as trade_value1.csv
	# Save FULL-PPR as trade_value2.csv
	trade_values = {}
	for table_id in ["trade_value0", "trade_value1", "trade_value2"]:
		html = open("static/trade_value/{}.csv".format(table_id)).readlines()		
		for row in html[4:]:
			data = row.split(",")
			value = float(data[2])
			for td in data[3:]:
				try:
					name = fix_name(td.lower().replace("'", ""))
					if name not in trade_values:
						trade_values[name] = []
					trade_values[name].append(value)
				except:
					pass

	with open("static/trade_value/trade_value.json", "w") as fh:
		json.dump(trade_values, fh, indent=4)

def read_trade_values():
	with open("static/trade_value/trade_value.json") as fh:
		returned_json = json.loads(fh.read())
	return returned_json

def write_borischen_extension():

	stats = {}
	positions = ["quarterback", "half-05-5-ppr-running-back", "half-05-5-ppr-wide-receiver", "half-05-5-ppr-tight-end", "kicker", "defense-dst"]
	player_ids = yahoo_stats.read_yahoo_ids()

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
						stats[player_ids[fix_name(name.lower().replace("'", ""))]] = tier
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


@extension.route('/extension')
def extension_route():

	if request.args.get("borischen"):
		return jsonify(tiers=read_borischen_extension(request.args.get("host")))

	is_espn = request.args.get("is_espn") == "true"
	is_nfl = request.args.get("is_nfl") == "true"
	rosters, translations = read_rosters.read_rosters()
	trade_values = read_trade_values()
	results_arr = []

	for team_idx in range(2):
		player_len = int(request.args.get("team_{}_len".format(team_idx)))

		for player_idx in range(player_len):
			player = request.args.get("team_{}_player_{}".format(team_idx, player_idx))
			try:
				name,team,pos,clicked = player.split(",")
			except:
				continue
			full_name = name.lower()
			if not is_nfl and not is_espn and pos != "DEF" and request.args.get("evaluate") == "false":
				try:
					full_name = translations[name+" "+team]
				except:
					continue
			elif is_espn or is_nfl:
				full_name = fix_name(full_name.replace("'", "").replace("/", ""))

			try:
				vals = [str(x) for x in trade_values[full_name.lower()]]
			except:
				vals = ["0","0","0"]

			results_arr.append({"team": team_idx, "full": full_name.title(), "full_val": float(vals[-1]),"vals": vals, "clicked": clicked})
	
	results_arr = sorted(results_arr, key=operator.itemgetter("full_val"), reverse=True)
	results = {"team0": [], "team1": []}
	for res in results_arr:
		results["team{}".format(res["team"])].append("{},{},{}".format(res["full"], "_".join(res["vals"]), res["clicked"]))
	return jsonify(team0=results["team0"], team1=results["team1"])

