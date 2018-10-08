
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
	elif name == "mark ingram ii":
		return "mark ingram"
	return name

def write_cron_trade_values():
	html = open("static/trade_value/trade_value.html")
	soup = BS(html.read(), "lxml")

	table_ids = ["1945815333", "1224738490", "559389759"]
	trade_values = {}
	for table_id in table_ids:
		rows = soup.find("div", id=table_id).find_all("tr")
		for row in rows[5:]:
			value = float(row.find("td", class_="s18").find("span").text)
			tds = row.find_all("td", class_="s19") + row.find_all("td", class_="s21")
			for td in tds:
				try:
					name = fix_name(td.find("span").text.lower().replace("'", ""))
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

@extension.route('/extension')
def extension_route():

	is_espn = request.args.get("is_espn") == "true"
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
			if not is_espn and pos != "DEF" and request.args.get("evaluate") == "false":
				try:
					full_name = translations[name+" "+team]
				except:
					continue
			elif is_espn:
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

