#from selenium import webdriver
from flask import *
from subprocess import call
from bs4 import BeautifulSoup as BS
from sys import platform
from datetime import datetime

import argparse
import glob
import json
import math
import operator
import os
import subprocess
import re
import time

ncaabprops_blueprint = Blueprint('ncaabprops', __name__, template_folder='views')

prefix = ""
if os.path.exists("/home/zhecht/fantasy"):
	# if on linux aka prod
	prefix = "/home/zhecht/fantasy/"

def teamTotals(today, schedule):
	with open(f"{prefix}static/ncaabreference/scores.json") as fh:
		scores = json.load(fh)
	totals = {}
	for date in scores:
		games = schedule[date]
		for team in scores[date]:
			opp = ""
			for game in games:
				if team in game.split(" @ "):
					opp = game.replace(team, "").replace(" @ ", "")
			if team not in totals:
				totals[team] = {"ppg": 0, "ppga": 0, "games": 0, "overs": [], "ttOvers": []}
			if opp not in totals:
				totals[opp] = {"ppg": 0, "ppga": 0, "games": 0, "overs": [], "ttOvers": []}
			totals[team]["games"] += 1
			totals[team]["ppg"] += scores[date][team]
			totals[team]["ppga"] += scores[date][opp]
			totals[team]["ttOvers"].append(str(scores[date][team]))
			totals[team]["overs"].append(str(scores[date][team] + scores[date][opp]))

	out = "team|ppg|ppga|overs|overs avg|ttOvers|TT avg\n"
	out += ":--|:--|:--|:--|:--|:--|:--\n"
	for game in schedule[today]:
		away, home = map(str, game.split(" @ "))
		ppg = round(totals[away]["ppg"] / totals[away]["games"], 1)
		ppga = round(totals[away]["ppga"] / totals[away]["games"], 1)
		overs = ",".join(totals[away]["overs"])
		oversAvg = round(sum([int(x) for x in totals[away]["overs"]]) / len(totals[away]["overs"]), 1)
		ttOvers = ",".join(totals[away]["ttOvers"])
		ttOversAvg = round(sum([int(x) for x in totals[away]["ttOvers"]]) / len(totals[away]["ttOvers"]), 1)
		out += f"{away}|{ppg}|{ppga}|{overs}|{oversAvg}|{ttOvers}|{ttOversAvg}\n"
		ppg = round(totals[home]["ppg"] / totals[home]["games"], 1)
		ppga = round(totals[home]["ppga"] / totals[home]["games"], 1)
		overs = ",".join(totals[home]["overs"])
		oversAvg = round(sum([int(x) for x in totals[home]["overs"]]) / len(totals[home]["overs"]), 1)
		ttOvers = ",".join(totals[home]["ttOvers"])
		ttOversAvg = round(sum([int(x) for x in totals[home]["ttOvers"]]) / len(totals[home]["ttOvers"]), 1)
		out += f"{home}|{ppg}|{ppga}|{overs}|{oversAvg}|{ttOvers}|{ttOversAvg}\n"
		out += "-|-|-|-|-|-|-\n"

	with open("out2", "w") as fh:
		fh.write(out)

def customPropData(propData):
	pass


@ncaabprops_blueprint.route('/getNCAABProps')
def getProps_route():
	res = []

	teams = request.args.get("teams") or ""
	if teams:
		teams = teams.lower().split(",")

	date = datetime.now()
	date = str(date)[:10]

	with open(f"{prefix}static/ncaabprops/dates/{date}.json") as fh:
		propData = json.load(fh)
	with open(f"{prefix}static/ncaabreference/totals.json") as fh:
		stats = json.load(fh)
	with open(f"{prefix}static/ncaabreference/averages.json") as fh:
		averages = json.load(fh)
	with open(f"{prefix}static/ncaabreference/lastYearStats.json") as fh:
		lastYearStats = json.load(fh)
	with open(f"{prefix}static/ncaabreference/schedule.json") as fh:
		schedule = json.load(fh)

	#propData = customPropData(propData)
	#teamTotals(date, schedule)

	props = []
	for team in propData:

		if teams and team not in teams:
			continue

		opp = ""
		if date in schedule:
			for ts in schedule[date]:
				ts = ts.split(" @ ")
				if team in ts:
					opp = ts[0] if ts[1] == team else ts[1]

		for propName in propData[team]:
			name = propName
			avgMin = 0
			if team in stats and name in stats[team] and stats[team][name]["gamesPlayed"]:
				avgMin = int(stats[team][name]["min"] / stats[team][name]["gamesPlayed"])
			for prop in propData[team][propName]:
				line = propData[team][propName][prop]["line"]
				avg = "-"

				if team in stats and name in stats[team] and stats[team][name]["gamesPlayed"]:
					val = 0
					if "+" in prop:
						for p in prop.split("+"):
							val += stats[team][name][p]
					elif prop in stats[team][name]:
						val = stats[team][name][prop]
					avg = round(val / stats[team][name]["gamesPlayed"], 1)
				# get best odds
				overOdds = underOdds = float('-inf')
				for book in propData[team][propName][prop]:
					if book == "line" or not propData[team][propName][prop][book]["over"]:
						continue

					line = propData[team][propName][prop]["line"][1:]
					over = propData[team][propName][prop][book]["over"]
					overLine = over.split(" ")[0][1:]
					overOdd = int(over.split(" ")[1][1:-1])
					if overLine == line and overOdd > overOdds:
						overOdds = overOdd

					under = propData[team][propName][prop][book].get("under", 0)
					if under:
						underLine = under.split(" ")[0][1:]
						underOdd = int(under.split(" ")[1][1:-1])
						if underLine == line and underOdd > underOdds:
							underOdds = underOdd

				if overOdds == float('-inf'):
					continue
				overOdds = str(overOdds)
				underOdds = str(underOdds)
				if not overOdds.startswith("-"):
					overOdds = "+"+overOdds
				if not underOdds.startswith("-"):
					underOdds = "+"+underOdds

				lastAvg = lastAvgMin = 0

				diff = diffAvg = 0
				if avg != "-" and line:
					diffAvg = round((avg / float(line) - 1), 2)
				if lastAvg and line:
					diff = round((lastAvg / float(line) - 1), 2)

				totalOver = totalGames = 0
				last5 = []
				if line and avgMin:
					files = sorted(glob.glob(f"{prefix}static/ncaabreference/{team}/*.json"), key=lambda k: datetime.strptime(k.split("/")[-1].replace(".json", ""), "%Y-%m-%d"), reverse=True)
					for file in files:
						with open(file) as fh:
							gameStats = json.load(fh)
						if name in gameStats:
							minutes = gameStats[name]["min"]
							if minutes > 0:
								totalGames += 1
								val = 0.0
								if "+" in prop:
									for p in prop.split("+"):
										val += gameStats[name][p]
								else:
									val = gameStats[name][prop]

								if len(last5) < 7:
									last5.append(str(int(val)))
								valPerMin = float(val / minutes)
								linePerMin = float(line) / avgMin
								#if valPerMin > linePerMin:
								if val > float(line):
									totalOver += 1 
				if totalGames:
					totalOver = round((totalOver / totalGames) * 100)

				props.append({
					"player": name.title(),
					"team": team.upper(),
					"opponent": opp,
					"propType": prop,
					"line": line or "-",
					"avg": avg,
					"avgMin": avgMin,
					"totalOver": totalOver,
					"last5": ",".join(last5),
					"overOdds": overOdds,
					"underOdds": underOdds
				})

	return jsonify(props)

@ncaabprops_blueprint.route('/ncaabprops')
def props_route():
	teams = request.args.get("teams") or ""
	return render_template("ncaabprops.html", teams=teams)

def writeProps(date):
	actionNetworkBookIds = {
		68: "draftkings",
		69: "fanduel"
	}
	propMap = {
		"3ptm": "core_bet_type_21_3fgm",
		"reb": "core_bet_type_23_rebounds",
		"ast": "core_bet_type_26_assists",
		"pts": "core_bet_type_27_points"
	}
	props = {}
	optionTypes = {}
	for prop in ["pts", "ast", "reb", "3ptm"]:

		path = f"{prefix}static/ncaabprops/{prop}.json"
		url = f"https://api.actionnetwork.com/web/v1/leagues/6/props/{propMap[prop]}?bookIds=69,68&date={date.replace('-', '')}"
		time.sleep(0.4)
		os.system(f"curl -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:106.0) Gecko/20100101 Firefox/106.0' -k \"{url}\" -o {path}")

		with open(path) as fh:
			j = json.load(fh)

		with open(path, "w") as fh:
			json.dump(j, fh, indent=4)

		if "markets" not in j:
			continue
		market = j["markets"][0]

		for option in market["rules"]["options"]:
			optionTypes[int(option)] = market["rules"]["options"][option]["option_type"].lower()

		teamIds = {}
		for row in market["teams"]:
			teamIds[row["id"]] = row["abbr"].lower()

		playerIds = {}
		for row in market["players"]:
			playerIds[row["id"]] = row["full_name"].lower()

		books = market["books"]
		for bookData in books:
			bookId = bookData["book_id"]
			if bookId not in actionNetworkBookIds:
				continue
			for oddData in bookData["odds"]:
				player = playerIds[oddData["player_id"]]
				team = teamIds[oddData["team_id"]]
				overUnder = optionTypes[oddData["option_type_id"]]
				book = actionNetworkBookIds[bookId]

				if team not in props:
					props[team] = {}
				if player not in props[team]:
					props[team][player] = {}
				if prop not in props[team][player]:
					props[team][player][prop] = {}
				if book not in props[team][player][prop]:
					props[team][player][prop][book] = {}
				props[team][player][prop][book][overUnder] = f"{overUnder[0]}{oddData['value']} ({oddData['money']})"
				if "line" not in props[team][player][prop]:
					props[team][player][prop]["line"] = f"o{oddData['value']}"
				elif oddData['value'] < float(props[team][player][prop]["line"][1:]):
					props[team][player][prop]["line"] = f"o{oddData['value']}"

	with open(f"{prefix}static/ncaabprops/dates/{date}.json", "w") as fh:
		json.dump(props, fh, indent=4)

def fixLines(props):
	pass

def writeTranslations(date):
	with open(f"{prefix}static/ncaabreference/translations.json") as fh:
		translations = json.load(fh)

	with open(f"{prefix}static/ncaabprops/{date}.json") as fh:
		props = json.load(fh)

	shortNames = translations.values()
	for idx, team in enumerate(props):
		if team not in shortNames:
			translations[idx] = team

	with open(f"{prefix}static/ncaabreference/translations.json", "w") as fh:
		json.dump(translations, fh, indent=4)

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("-c", "--cron", action="store_true", help="Start Cron Job")
	parser.add_argument("-d", "--date", help="Date")
	parser.add_argument("--zero", help="Zero CustomProp Odds", action="store_true")
	parser.add_argument("-w", "--week", help="Week", type=int)

	args = parser.parse_args()

	date = args.date
	if not date:
		date = datetime.now()
		date = str(date)[:10]

	#writeTranslations(date)

	if args.cron:
		writeProps(date)