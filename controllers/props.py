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

try:
	from controllers.read_rosters import *
	from controllers.functions import *
except:
	from functions import *
	from read_rosters import *

props_blueprint = Blueprint('props', __name__, template_folder='views')

prefix = ""
if os.path.exists("/home/zhecht/fantasy"):
	# if on linux aka prod
	prefix = "/home/zhecht/fantasy/"

pffTeamTranslations = {"ARZ": "CRD", "BLT": "RAV", "CLV": "CLE", "GB": "GNB", "HST": "HTX", "IND": "CLT", "KC": "KAN", "LAC": "SDG", "LA": "RAM", "LV": "RAI", "NO": "NOR", "NE": "NWE", "SF": "SFO", "TB": "TAM", "TEN": "OTI"}

def getProfootballReferenceTeam(team):
	if team == "arz":
		return "crd"
	elif team == "blt":
		return "rav"
	elif team == "clv":
		return "cle"
	elif team == "gb":
		return "gnb"
	elif team == "hst":
		return "htx"
	elif team == "ind":
		return "clt"
	elif team == "kc":
		return "kan"
	elif team == "la":
		return "ram"
	elif team == "lac":
		return "sdg"
	elif team == "lv":
		return "rai"
	elif team == "no":
		return "nor"
	elif team == "ne":
		return "nwe"
	elif team == "sf":
		return "sfo"
	elif team == "tb":
		return "tam"
	elif team == "ten":
		return "oti"
	return team

def getYahooTeam(team):
	if team == "ARZ":
		return "ARI"
	elif team == "BLT":
		return "BAL"
	elif team == "CLV":
		return "CLE"
	elif team == "HST":
		return "HOU"
	elif team == "LA":
		return "LAR"
	return team

@props_blueprint.route('/getProps')
def getProps_route():
	res = []

	with open(f"{prefix}static/props.json") as fh:
		propData = json.load(fh)

	players_on_teams,translations = read_rosters()
	fa,fa_translations = read_FA_translations()
	translations = {**translations, **fa_translations}

	for nameRow in propData:
		name = " ".join(nameRow.split(" ")[:-1])
		team = nameRow.split(" ")[-1]
		with open(f"{prefix}static/profootballreference/{getProfootballReferenceTeam(team.lower())}/stats.json") as fh:
			stats = json.load(fh)

		playerStats = {}
		if name+" "+getYahooTeam(team) not in translations:
			#print(name)
			player = name
		else:
			player = translations[name+" "+getYahooTeam(team)]
			if player in stats:
				gameLogs = stats[player]
				gamesPlayed = 0
				for wk in gameLogs:
					if wk == "tot" or not gameLogs[wk].get("snap_counts", 0):
						continue
					gamesPlayed += 1
				playerStats = gameLogs
				playerStats["tot"]["gamesPlayed"] = gamesPlayed

		for typ in propData[nameRow]:
			res.append({
				"player": player.title(),
				"team": getYahooTeam(team),
				"hit": True,
				"opponent": getYahooTeam(propData[nameRow][typ]["opponent"]),
				"propType": typ,
				"line": propData[nameRow][typ]["line"],
				"sideOneType": propData[nameRow][typ]["sideOneType"],
				"sideOneOdds": propData[nameRow][typ]["sideOneOdds"],
				"sideTwoType": propData[nameRow][typ]["sideTwoType"],
				"sideTwoOdds": propData[nameRow][typ]["sideTwoOdds"],
				"stats": playerStats
			})

	return jsonify(res)

@props_blueprint.route('/props', methods=["POST"])
def props_post_route():
    favorites = request.args.get("favorites") 
    favs = []
    for data in favorites.split(";"):
    	favs.append({
    		"player": data.split("*")[0],
    		"propType": data.split("*")[1]
    	})

    with open(f"{prefix}static/favorite_props.json", "w") as fh:
    	json.dump(favs, fh, indent=4)
    return jsonify(success=1)

@props_blueprint.route('/props')
def props_route():
	return render_template("props.html", curr_week=CURR_WEEK)


def writeProps():
	players_on_teams,translations = read_rosters()
	with open(f"{prefix}static/props/wk{CURR_WEEK+1}.csv") as fh:
		lines = [line.strip() for line in fh.readlines() if line.strip()]

	fields = [
		"propType", "player", "position", "team", "opponent", "line", "sideOneType", "sideOneOdds", "sideTwoOdds", "sideTwoType"
	]

	idxs = {}
	headers = lines[0].split(",")
	for field in fields:
		idxs[field] = headers.index(f'"{field}"')

	props = {}
	for line in lines[1:]:
		data = line.split(",")
		currProps = {}
		for field in idxs:
			currProps[field] = data[idxs[field]].replace('"', '')

		player = currProps["player"]+" "+currProps["team"]
		#player = translations[player]
		if player not in props:
			props[player] = {}


		props[player][currProps["propType"]] = currProps

	with open(f"{prefix}static/props.json", "w") as fh:
			json.dump(props, fh, indent=4)



if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("-c", "--cron", action="store_true", help="Start Cron Job")

	args = parser.parse_args()
	if args.cron:
		writeProps()