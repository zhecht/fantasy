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

nbaprops_blueprint = Blueprint('nbaprops', __name__, template_folder='views')

prefix = ""
if os.path.exists("/home/zhecht/fantasy"):
	# if on linux aka prod
	prefix = "/home/zhecht/fantasy/"

def fixNBATeam(team):
	if team == "gsw":
		return "gs"
	elif team == "nop":
		return "no"
	elif team == "sas":
		return "sa"
	elif team == "nyk":
		return "ny"
	elif team == "uta":
		return "utah"
	return team

def teamTotals(today, schedule):
	with open(f"{prefix}static/basketballreference/scores.json") as fh:
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
	over = True

	with open(f"{prefix}static/nbaprops/customProps.json") as fh:
		data = json.load(fh)

	propData = {}
	for team in data:
		if team not in propData:
			propData[team] = {}
		for player in data[team]:
			propData[team][player] = {}
			for prop in data[team][player]:
				idx = 0 if over else 1
				lines = data[team][player][prop]["line"]
				odds = data[team][player][prop]["odds"]
				overLine = f"{lines[0]} ({odds[0]})"
				underLine = ""
				line = lines[0]
				if len(lines) > 1:
					underLine = f"{lines[1]} ({odds[1]})"
					if not over:
						line = lines[1]

				propData[team][player][prop] = {
					"line": line,
					"draftkings": {
						"over": overLine,
						"under": underLine 
					}
				}

	return propData


@nbaprops_blueprint.route('/getNBAProps')
def getProps_route():
	res = []

	date = datetime.now()
	date = str(date)[:10]

	with open(f"{prefix}static/nbaprops/dates/{date}.json") as fh:
		propData = json.load(fh)
	with open(f"{prefix}static/basketballreference/totals.json") as fh:
		stats = json.load(fh)
	with open(f"{prefix}static/basketballreference/averages.json") as fh:
		averages = json.load(fh)
	with open(f"{prefix}static/basketballreference/rankings.json") as fh:
		rankings = json.load(fh)
	with open(f"{prefix}static/basketballreference/lastYearStats.json") as fh:
		lastYearStats = json.load(fh)
	with open(f"{prefix}static/basketballreference/schedule.json") as fh:
		schedule = json.load(fh)
	with open(f"{prefix}static/basketballreference/roster.json") as fh:
		roster = json.load(fh)

	#propData = customPropData(propData)
	teamTotals(date, schedule)

	props = []
	for team in propData:
		espnTeam = fixNBATeam(team)
		opp = ""
		if date in schedule:
			for teams in schedule[date]:
				teams = teams.split(" @ ")
				if espnTeam in teams:
					if teams.index(espnTeam) == 0:
						opp = teams[1]
					else:
						opp = teams[0]

		if espnTeam.lower() not in ["utah", "atl", "det", "bos", "ny", "bkn", "hou", "tor"]:
			#continue
			pass

		for propName in propData[team]:
			name = propName.replace("-", " ").replace(".", "").replace("'", "")
			avgMin = 0
			if espnTeam in stats and name in stats[espnTeam] and stats[espnTeam][name]["gamesPlayed"]:
				avgMin = int(stats[espnTeam][name]["min"] / stats[espnTeam][name]["gamesPlayed"])
			for prop in propData[team][propName]:
				line = propData[team][propName][prop]["line"]
				avg = "-"

				if "+" in prop:
					#continue
					pass
				if prop in ["stl", "blk", "stl+blk", "3ptm"]:
					#continue
					pass

				if espnTeam in stats and name in stats[espnTeam] and stats[espnTeam][name]["gamesPlayed"]:
					val = 0
					if "+" in prop:
						for p in prop.split("+"):
							val += stats[espnTeam][name][p]
					elif prop in stats[espnTeam][name]:
						val = stats[espnTeam][name][prop]
					avg = round(val / stats[espnTeam][name]["gamesPlayed"], 1)
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
					pass
					
				overOdds = str(overOdds)
				underOdds = str(underOdds)
				if not overOdds.startswith("-"):
					overOdds = "+"+overOdds
				if not underOdds.startswith("-"):
					underOdds = "+"+underOdds

				lastAvg = lastAvgMin = 0
				proj = 0
				if name in averages[espnTeam] and averages[espnTeam][name]:
					lastAvgMin = averages[espnTeam][name]["min"]
					if "+" in prop:
						for p in prop.split("+"):
							lastAvg += averages[espnTeam][name][p]
					elif prop in averages[espnTeam][name]:
						lastAvg = averages[espnTeam][name][prop]
					proj = lastAvg / lastAvgMin
					lastAvg = round(lastAvg, 1)

				diff = diffAvg = 0
				if avg != "-" and line:
					diffAvg = round((avg / float(line) - 1), 2)
				if lastAvg and line:
					diff = round((lastAvg / float(line) - 1), 2)

				lastTotalOver = lastTotalGames = 0
				if line and avgMin and name in lastYearStats[espnTeam] and lastYearStats[espnTeam][name]:
					for dt in lastYearStats[espnTeam][name]:
						minutes = lastYearStats[espnTeam][name][dt]["min"]
						if minutes > 0:
							lastTotalGames += 1
							if "+" in prop:
								val = 0.0
								for p in prop.split("+"):
									val += lastYearStats[espnTeam][name][dt][p]
							else:
								val = lastYearStats[espnTeam][name][dt][prop]
							valPerMin = float(val / minutes)
							linePerMin = float(line) / avgMin
							if valPerMin > linePerMin:
								lastTotalOver += 1
				if lastTotalGames:
					lastTotalOver = round((lastTotalOver / lastTotalGames) * 100)

				totalOver = totalGames = avgVariance = 0
				last5 = []
				if line and avgMin:
					files = sorted(glob.glob(f"{prefix}static/basketballreference/{espnTeam}/*.json"), key=lambda k: datetime.strptime(k.split("/")[-1].replace(".json", ""), "%Y-%m-%d"), reverse=True)
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

								avgVariance += (val / float(line)) - 1
								if len(last5) < 7:
									last5.append(str(int(val)))
								valPerMin = float(val / minutes)
								linePerMin = float(line) / avgMin
								#if valPerMin > linePerMin:
								if val > float(line):
									totalOver += 1 
				if totalGames:
					totalOver = round((totalOver / totalGames) * 100)
					avgVariance = round(avgVariance / totalGames, 1)

				diffAbs = 0
				if avgMin:
					proj = round(proj*float(avgMin), 1)
					if line:
						diffAbs = round((proj / float(line) - 1), 2)
					else:
						diffAbs = diffAvg

				rank = oppRank = ""
				rankVal = oppRankVal = ""
				rankingsProp = convertRankingsProp(prop)
				if rankingsProp in rankings[opp]:
					rankVal = str(rankings[espnTeam][rankingsProp]["season"])
					oppRankVal = str(rankings[opp]["o"+rankingsProp]["season"])
					if "%" in rankingsProp:
						rankVal += "%"
						oppRankVal += "%"
					rank = rankings[espnTeam][rankingsProp]['rank']
					oppRank = rankings[opp]['o'+rankingsProp]['rank']

				props.append({
					"player": name.title(),
					"team": espnTeam.upper(),
					"opponent": opp,
					"position": roster[espnTeam][name],
					"propType": prop,
					"line": line or "-",
					"avg": avg,
					"diffAvg": diffAvg,
					"diffAbs": abs(diffAbs),
					"lastAvg": lastAvg,
					"diff": diff,
					"avgMin": avgMin,
					"proj": proj,
					"avgVariance": avgVariance,
					"rank": rank,
					"oppRank": oppRank,
					"rankVal": rankVal,
					"oppRankVal": oppRankVal,
					"lastAvgMin": lastAvgMin,
					"totalOver": totalOver,
					"lastTotalOver": lastTotalOver,
					"last5": ",".join(last5),
					"overOdds": overOdds,
					"underOdds": underOdds
				})

	return jsonify(props)

def convertRankingsProp(prop):
	if "+" in prop:
		return prop
	elif prop == "3ptm":
		return "3pt%"
	elif prop in ["blk", "stl"]:
		return prop+"pg"
	elif prop == "pts":
		return "fgpg"
	return prop[0]+"pg"

@nbaprops_blueprint.route('/nbaprops')
def props_route():
	prop = ""
	if request.args.get("prop"):
		prop = request.args.get("prop").replace(" ", "+")
	return render_template("nbaprops.html", prop=prop)

def writeProps(date):
	url = "https://www.actionnetwork.com/nba/props/points"

	props = {}

	for prop in ["pts", "ast", "reb", "blk", "stl", "pts+ast", "pts+reb", "pts+reb+ast", "reb+ast", "stl+blk", "3ptm"]:
		path = f"{prefix}static/nbaprops/{prop}.html"
		#os.system(f"curl -k \"{url}\" -o {path}")
		with open(path) as fh:
			soup = BS(fh.read(), "lxml")

		books = ["fanduel", "betmgm", "draftkings", "caesars"]
		#books = ["fanduel", "betmgm", "draftkings"]

		for row in soup.findAll("tr")[1:]:
			name = row.find("div", class_="total-prop-row__player-name").text.lower()
			team = row.find("div", class_="total-prop-row__player-team").text.lower()
			if team not in props:
				props[team] = {}

			if name not in props[team]:
				props[team][name] = {}
			if prop not in props[team][name]:
				props[team][name][prop] = {}

			props[team][name][prop] = {"line": {}}
			for idx, td in enumerate(row.findAll("td")[2:-4]):
				odds = td.findAll("div", class_="book-cell__odds")
				over = under = ""
				line = ""
				if odds[0].text != "N/A":
					over = odds[0].findAll("span")[0].text+" ("+odds[0].findAll("span")[1].text+")"
					line = odds[0].findAll("span")[0].text
				if odds[1].text != "N/A":
					under = odds[1].findAll("span")[0].text+" ("+odds[1].findAll("span")[1].text+")"
				book = books[idx]
				if book == "betmgm":
					continue

				if line and line not in props[team][name][prop]["line"]:
					props[team][name][prop]["line"][line] = 0
				if line:
					props[team][name][prop]["line"][line] += 1

				props[team][name][prop][book] = {
					"over": over,
					"under": under
				}
			lines = sorted(props[team][name][prop]["line"])
			if lines:
				props[team][name][prop]["line"] = lines[0]

	fixLines(props)
	with open(f"{prefix}static/nbaprops/dates/{date}.json", "w") as fh:
		json.dump(props, fh, indent=4)

def fixLines(props):
	pass

def zeroProps():
	with open(f"{prefix}static/nbaprops/customProps.json") as fh:
		data = json.load(fh)
	for team in data:
		for player in data[team]:
			for prop in data[team][player]:
				data[team][player][prop]["odds"] = ["-0"]*len(data[team][player][prop]["odds"])
	with open(f"{prefix}static/nbaprops/customProps.json", "w") as fh:
		json.dump(data, fh, indent=4)
	

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

	if args.cron:
		writeProps(date)
	elif args.zero:
		zeroProps()