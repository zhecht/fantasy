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
	from controllers.profootballreference import *
	from controllers.read_rosters import *
	from controllers.functions import *
except:
	from functions import *
	from profootballreference import *
	from read_rosters import *

props_blueprint = Blueprint('props', __name__, template_folder='views')

prefix = ""
if os.path.exists("/home/zhecht/fantasy"):
	# if on linux aka prod
	prefix = "/home/zhecht/fantasy/"

pffTeamTranslations = {"ARZ": "CRD", "BLT": "RAV", "CLV": "CLE", "GB": "GNB", "HST": "HTX", "IND": "CLT", "KC": "KAN", "LAC": "SDG", "LA": "RAM", "LV": "RAI", "NO": "NOR", "NE": "NWE", "SF": "SFO", "TB": "TAM", "TEN": "OTI"}

def getProfootballReferenceTeam(team):
	if team == "arz" or team == "ari":
		return "crd"
	elif team == "bal" or team == "blt":
		return "rav"
	elif team == "clv":
		return "cle"
	elif team == "gb":
		return "gnb"
	elif team == "hst" or team == "hou":
		return "htx"
	elif team == "ind":
		return "clt"
	elif team == "kc":
		return "kan"
	elif team == "la" or team == "lar":
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
	elif team == "wsh":
		return "was"
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
	elif team == "WSH":
		return "WAS"
	return team

def getDefPropsData():
	with open(f"{prefix}static/props/wk{CURR_WEEK+1}_def.json") as fh:
		propData = json.load(fh)

	res = []
	for nameRow in propData:
		name = " ".join(nameRow.split(" ")[:-1])
		name = fixName(name.lower())
		team = nameRow.split(" ")[-1]

		with open(f"{prefix}static/profootballreference/{getProfootballReferenceTeam(team.lower())}/stats.json") as fh:
			stats = json.load(fh)

		playerStats = {}
		if name not in stats:
			pass
		else:
			gameLogs = stats[name]
			gamesPlayed = 0
			for wk in gameLogs:
				if wk == "tot" or not gameLogs[wk].get("snap_counts", 0):
					continue
				gamesPlayed += 1
			playerStats = gameLogs
			playerStats["tot"]["gamesPlayed"] = gamesPlayed

		overOdds = underOdds = float('-inf')
		for book in propData[nameRow]:
			if book == "line" or not propData[nameRow][book]["over"]:
				continue

			line = propData[nameRow]["line"][1:]
			over = propData[nameRow][book]["over"]
			overLine = over.split(" ")[0][1:]
			overOdd = int(over.split(" ")[1][1:-1])
			if overLine == line and overOdd > overOdds:
				overOdds = overOdd

			under = propData[nameRow][book]["under"]
			underLine = under.split(" ")[0][1:]
			underOdd = int(under.split(" ")[1][1:-1])
			if underLine == line and underOdd > underOdds:
				underOdds = underOdd

		overOdds = str(overOdds)
		underOdds = str(underOdds)
		if not overOdds.startswith("-"):
			overOdds = "+"+overOdds
		if not underOdds.startswith("-"):
			underOdds = "+"+underOdds

		line = propData[nameRow]["line"]
		if line:
			line = line[1:]
		res.append({
			"player": name.title(),
			"team": getYahooTeam(team),
			"hit": True,
			"opponent": get_opponents(getProfootballReferenceTeam(team.lower()))[CURR_WEEK],
			"propType": "tackles_combined",
			"line": line or "-",
			"overOdds": "over ("+overOdds+")",
			"underOdds": "under ("+underOdds+")",
			"stats": playerStats
		})
	return res

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
			overOdds = propData[nameRow][typ]["sideOneOdds"]
			underOdds = propData[nameRow][typ]["sideTwoOdds"]
			if not overOdds.startswith("-"):
				overOdds = "+"+overOdds
			if not underOdds.startswith("-"):
				underOdds = "+"+underOdds

			res.append({
				"player": player.title(),
				"team": getYahooTeam(team),
				"hit": True,
				"opponent": getYahooTeam(propData[nameRow][typ]["opponent"]),
				"propType": typ,
				"line": propData[nameRow][typ]["line"] or "-",
				"overOdds": propData[nameRow][typ]["sideOneType"]+ " ("+overOdds+")",
				"underOdds": propData[nameRow][typ]["sideTwoType"]+ " ("+underOdds+")",
				"stats": playerStats
			})

	res.extend(getDefPropsData())
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

def writeDefProps(week):
	url = "https://www.actionnetwork.com/nfl/props/tackles-assists"
	path = "out.html"
	os.system(f"curl -k \"{url}\" -o {path}")
	with open(path) as fh:
		soup = BS(fh.read(), "lxml")

	books = ["fanduel", "betmgm", "draftkings", "caesars"]

	props = {}

	for row in soup.findAll("tr")[1:]:
		name = row.find("div", class_="option-prop-row__player-name").text
		team = row.find("div", class_="option-prop-row__player-team").text
		props[name.lower()+" "+team] = {"line": {}}
		for idx, td in enumerate(row.findAll("td")[1:-3]):
			odds = td.findAll("div", class_="book-cell__odds")
			over = under = ""
			line = ""
			if odds[0].text != "N/A":
				over = odds[0].findAll("span")[0].text+" ("+odds[0].findAll("span")[1].text+")"
				line = odds[0].findAll("span")[0].text
			if odds[1].text != "N/A":
				under = odds[1].findAll("span")[0].text+" ("+odds[1].findAll("span")[1].text+")"
			book = books[idx]

			if line and line not in props[name.lower()+" "+team]["line"]:
				props[name.lower()+" "+team]["line"][line] = 0
			if line:
				props[name.lower()+" "+team]["line"][line] += 1

			props[name.lower()+" "+team][book] = {
				"over": over,
				"under": under
			}
		lines = sorted(props[name.lower()+" "+team]["line"])
		if lines:
			props[name.lower()+" "+team]["line"] = lines[0]

	with open(f"{prefix}static/props/wk{week}_def.json", "w") as fh:
		json.dump(props, fh, indent=4)


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
	parser.add_argument("-w", "--week", help="Week", type=int)

	args = parser.parse_args()
	week = CURR_WEEK

	if args.week:
		week = args.week
	if args.cron:
		#writeProps()
		writeDefProps(week)