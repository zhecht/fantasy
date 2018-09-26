
from flask import *
from bs4 import BeautifulSoup as BS

import json
import operator
import urllib

try:
  import controllers.read_rosters as read_rosters
except:
  import read_rosters


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
	elif name == "odell beckham":
		return "odell beckham jr."
	return name

def write_cron_trade_values():
	table_id = "1653199057"

	html = open("static/trade_value/trade_value.html")
	soup = BS(html.read(), "lxml")
	rows = soup.find("div", id=table_id).find_all("tr")

	trade_values = {}
	for row in rows[5:]:
		#print(row)
		value = float(row.find("td", class_="s18").find("span").text)
		tds = row.find_all("td", class_="s19")
		for td in tds:
			try:
				name = fix_name(td.find("span").text.lower().replace("'", ""))
				trade_values[name] = value
			except:
				pass

	with open("static/trade_value/trade_value.json", "w") as fh:
		json.dump(trade_values, fh, indent=4)

def read_trade_values():
	with open("static/trade_value/trade_value.json") as fh:
		returned_json = json.loads(fh.read())
	return returned_json

@extension.route('/extension')
def extension_route():
	rosters, translations = read_rosters.read_rosters()
	trade_values = read_trade_values()	
	results_arr = []

	for team_idx in range(2):
		player_len = int(request.args.get("team_{}_len".format(team_idx)))

		for player_idx in range(player_len):
			player = request.args.get("team_{}_player_{}".format(team_idx, player_idx))
			try:
				name,team,pos = player.split(",")
			except:
				continue
			full_name = name.lower()

			if pos != "DEF":
				try:
					full_name = translations[name+" "+team]
				except:
					continue
			try:
				val = trade_values[full_name.lower()]
			except:
				val = 0
			results_arr.append({"team": team_idx, "full": full_name.title(), "val": val})
	
	results_arr = sorted(results_arr, key=operator.itemgetter("val"), reverse=True)
	results = {"team0": [], "team1": []}
	for res in results_arr:
		results["team{}".format(res["team"])].append("{},{}".format(res["full"], res["val"]))
	return jsonify(team0=results["team0"], team1=results["team1"])

