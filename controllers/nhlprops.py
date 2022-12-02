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

nhlprops_blueprint = Blueprint('nhlprops', __name__, template_folder='views')

prefix = ""
if os.path.exists("/home/zhecht/fantasy"):
	# if on linux aka prod
	prefix = "/home/zhecht/fantasy/"

def fixNBATeam(team):
	return team

def convertProp(prop):
	if prop == "sog":
		return "s"
	elif prop == "goals":
		return "g"
	return prop

@nhlprops_blueprint.route('/getNHLProps')
def getProps_route():
	res = []

	teams = request.args.get("teams") or ""
	if teams:
		teams = teams.lower().split(",")
	alt = request.args.get("alt") or ""

	date = datetime.now()
	date = str(date)[:10]
	if request.args.get("date"):
		date = request.args.get("date")

	with open(f"{prefix}static/nhlprops/dates/{date}.json") as fh:
		propData = json.load(fh)
	with open(f"{prefix}static/hockeyreference/totals.json") as fh:
		stats = json.load(fh)
	with open(f"{prefix}static/hockeyreference/averages.json") as fh:
		averages = json.load(fh)
	with open(f"{prefix}static/hockeyreference/lastYearStats.json") as fh:
		lastYearStats = json.load(fh)
	with open(f"{prefix}static/hockeyreference/schedule.json") as fh:
		schedule = json.load(fh)

	fixLines(propData)

	props = []
	for team in propData:
		espnTeam = fixNBATeam(team)

		opp = ""
		if date in schedule:
			for t in schedule[date]:
				t = t.split(" @ ")
				if espnTeam in t:
					if t.index(espnTeam) == 0:
						opp = t[1]
					else:
						opp = t[0]

		if teams and team not in teams:
			continue

		for propName in propData[team]:
			shortFirstName = propName.split(" ")[0][0]
			restName = " ".join(propName.title().split(" ")[1:])
			name = f"{shortFirstName.upper()}. {restName.replace('-', ' ')}"
			avgMin = 0
			if espnTeam in stats and name in stats[espnTeam] and stats[espnTeam][name]["gamesPlayed"]:
				avgMin = int(stats[espnTeam][name]["toi"] / stats[espnTeam][name]["gamesPlayed"])
			for prop in propData[team][propName]:
				convertedProp = convertProp(prop)
				line = propData[team][propName][prop]["line"]
				avg = 0

				if espnTeam in stats and name in stats[espnTeam] and stats[espnTeam][name]["gamesPlayed"]:
					val = 0
					if convertedProp == "pts":
						val = stats[espnTeam][name]["g"] + stats[espnTeam][name]["a"]
					elif convertedProp in stats[espnTeam][name]:
						val = stats[espnTeam][name][convertedProp]
					avg = round(val / stats[espnTeam][name]["gamesPlayed"], 2)
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

					under = propData[team][propName][prop][book]["under"]
					if under:
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

				lastAvg = lastAvgMin = 0
				proj = 0
				if name in averages[espnTeam] and averages[espnTeam][name]:
					lastAvgMin = averages[espnTeam][name]["toi/g"]
					if convertedProp in averages[espnTeam][name]:
						lastAvg = averages[espnTeam][name][convertedProp]
					lastAvg = lastAvg / averages[espnTeam][name]["gamesPlayed"]
					proj = lastAvg / lastAvgMin
					lastAvg = round(lastAvg, 2)

				diff = diffAvg = 0
				if avg and line:
					diffAvg = round((avg / float(line) - 1), 2)
				if lastAvg and line:
					diff = round((lastAvg / float(line) - 1), 2)

				lastTotalOver = lastTotalGames = 0
				if line and avgMin and name in lastYearStats[espnTeam] and lastYearStats[espnTeam][name]:
					for d in lastYearStats[espnTeam][name]:
						minutes = lastYearStats[espnTeam][name][d]["toi/g"]
						if minutes > 0 and convertedProp in lastYearStats[espnTeam][name][d]:
							lastTotalGames += 1
							val = lastYearStats[espnTeam][name][d][convertedProp]
							valPerMin = float(val / minutes)
							linePerMin = float(line) / avgMin
							if valPerMin > linePerMin:
								lastTotalOver += 1
				if lastTotalGames:
					lastTotalOver = round((lastTotalOver / lastTotalGames) * 100)

				totalOver = totalOverLast5 = totalGames = 0
				last5 = []
				hit = False
				if line and avgMin:
					files = sorted(glob.glob(f"{prefix}static/hockeyreference/{espnTeam}/*.json"), key=lambda k: datetime.strptime(k.split("/")[-1].replace(".json", ""), "%Y-%m-%d"), reverse=True)
					for file in files:
						chkDate = file.split("/")[-1].replace(".json","")
						with open(file) as fh:
							gameStats = json.load(fh)
						if name in gameStats:
							minutes = gameStats[name]["toi"]
							if minutes > 0:
								totalGames += 1
								val = 0.0
								if convertedProp == "pts":
									val = gameStats[name]["a"] + gameStats[name]["g"]
								elif convertedProp in gameStats[name]:
									val = gameStats[name][convertedProp]

								if chkDate == date:
									if val > float(line):
										hit = True
									continue

								if len(last5) < 10:
									last5.append(str(int(val)))
								valPerMin = float(val / minutes)
								linePerMin = float(line) / avgMin
								if float(val) > float(line):
									totalOver += 1
									if len(last5) <= 5:
										totalOverLast5 += 1
								#if valPerMin > linePerMin:
								#	totalOver += 1 
				if totalGames:
					totalOver = round((totalOver / totalGames) * 100)
					last5Size = len(last5) if len(last5) < 5 else 5
					totalOverLast5 = round((totalOverLast5 / last5Size) * 100)

				diffAbs = 0
				if avgMin:
					proj = round(proj*float(avgMin), 1)
					if line:
						diffAbs = round((proj / float(line) - 1), 2)
					else:
						diffAbs = diffAvg

				props.append({
					"player": propName.title(),
					"team": espnTeam.upper(),
					"opponent": opp,
					"propType": prop,
					"line": line or "-",
					"avg": avg,
					"hit": hit,
					"diffAvg": diffAvg,
					"diffAbs": abs(diffAbs),
					"lastAvg": lastAvg,
					"diff": diff,
					"avgMin": avgMin,
					"proj": proj,
					"lastAvgMin": lastAvgMin,
					"totalOver": totalOver,
					"totalOverLast5": totalOverLast5,
					"lastTotalOver": lastTotalOver,
					"last5": ",".join(last5),
					"overOdds": overOdds,
					"underOdds": underOdds
				})

	teamTotals()
	write_csvs(props)
	return jsonify(props)

def teamTotals():
	today = datetime.now()
	today = str(today)[:10]

	with open(f"{prefix}static/hockeyreference/schedule.json") as fh:
		schedule = json.load(fh)
	with open(f"{prefix}static/hockeyreference/scores.json") as fh:
		scores = json.load(fh)

	totals = {}
	dates = sorted(schedule.keys(), key=lambda k: datetime.strptime(k, "%Y-%m-%d"), reverse=True)
	for date in dates:
		for game in schedule[date]:
			gameSp = game.split(" @ ")
			for idx, team in enumerate(gameSp):
				opp = gameSp[0] if idx == 1 else gameSp[1]

				if date not in scores or team not in scores[date]:
					continue

				if team not in totals:
					totals[team] = {"gpg": 0, "gpga": 0, "games": 0, "overs": [], "ttOvers": [], "opp_ttOvers": []}
				totals[team]["games"] += 1
				totals[team]["gpg"] += scores[date][team]
				totals[team]["gpga"] += scores[date][opp]
				totals[team]["ttOvers"].append(str(scores[date][team]))
				totals[team]["opp_ttOvers"].append(str(scores[date][opp]))
				totals[team]["overs"].append(str(scores[date][team] + scores[date][opp]))

	out = "\t".join([x.upper() for x in ["team", "gpg", "tt overs", "gpga", "opp tt overs", "overs avg", "overs"]]) + "\n"
	cutoff = 10
	for game in schedule[today]:
		away, home = map(str, game.split(" @ "))
		gpg = round(totals[away]["gpg"] / totals[away]["games"], 1)
		gpga = round(totals[away]["gpga"] / totals[away]["games"], 1)
		overs = ",".join(totals[away]["overs"][:cutoff])
		oversAvg = round(sum([int(x) for x in totals[away]["overs"]]) / len(totals[away]["overs"]), 1)
		ttOvers = ",".join(totals[away]["ttOvers"][:cutoff])
		opp_ttOvers = ",".join(totals[away]["opp_ttOvers"][:cutoff])

		out += "\t".join([away.upper(), str(gpg), ttOvers, str(gpga), opp_ttOvers, str(oversAvg), overs]) + "\n"

		gpg = round(totals[home]["gpg"] / totals[home]["games"], 1)
		gpga = round(totals[home]["gpga"] / totals[home]["games"], 1)
		overs = ",".join(totals[home]["overs"][:cutoff])
		oversAvg = round(sum([int(x) for x in totals[home]["overs"]]) / len(totals[home]["overs"]), 1)
		ttOvers = ",".join(totals[home]["ttOvers"][:cutoff])
		opp_ttOvers = ",".join(totals[home]["opp_ttOvers"][:cutoff])
		out += "\t".join([home.upper(), str(gpg), ttOvers, str(gpga), opp_ttOvers, str(oversAvg), overs]) + "\n"
		out += "\t".join(["-"]*7) + "\n"

	with open(f"{prefix}static/nhlprops/csvs/totals.csv", "w") as fh:
		fh.write(out)


def write_csvs(props):
	csvs = {}
	splitProps = {"full": []}
	headers = "\t".join(["NAME","TEAM","PROP","LINE","SZN AVG","% OVER","L5 % OVER","LAST 10 GAMES","LAST YR % OVER","OVER", "UNDER"])
	reddit = "|".join(headers.split("\t"))
	reddit += "\n:--|:--|:--|:--|:--|:--|:--|:--|:--|:--|:--"

	for row in props:
		if row["propType"] not in splitProps:
			splitProps[row["propType"]] = []

		if row["overOdds"] == '-inf':
			continue

		splitProps[row["propType"]].append(row)
		splitProps["full"].append(row)

	for prop in splitProps:
		csvs[prop] = headers
		rows = sorted(splitProps[prop], key=lambda k: (k["totalOverLast5"], k["totalOver"]), reverse=True)
		for row in rows:
			overOdds = row["overOdds"]
			underOdds = row["underOdds"]
			if int(overOdds) > 0:
				overOdds = "'"+overOdds
			if int(underOdds) > 0:
				underOdds = "'"+underOdds
			csvs[prop] += "\n" + "\t".join([row["player"], row["team"], row["propType"], str(row["line"]), str(row["avg"]), f"{row['totalOver']}%", f"{row['totalOverLast5']}%", row["last5"], f"{row['lastTotalOver']}%",overOdds, underOdds])

	# add full rows
	csvs["full"] = headers
	rows = sorted(splitProps["full"], key=lambda k: (k["player"]))
	for row in rows:
		overOdds = row["overOdds"]
		underOdds = row["underOdds"]
		if int(overOdds) > 0:
			overOdds = "'"+overOdds
		if int(underOdds) > 0:
			underOdds = "'"+underOdds
		csvs["full"] += "\n" + "\t".join([row["player"], row["team"], row["propType"], str(row["line"]), str(row["avg"]), f"{row['totalOver']}%", row["last5"], f"{row['lastTotalOver']}%",overOdds, underOdds])

	# add top 4 to reddit
	for prop in ["sog", "pts"]:
		rows = sorted(splitProps[prop], key=lambda k: (k["totalOverLast5"], k["totalOver"]), reverse=True)
		for row in rows[:4]:
			overOdds = row["overOdds"]
			underOdds = row["underOdds"]
			reddit += "\n" + "|".join([row["player"], row["team"], row["propType"], str(row["line"]), str(row["avg"]), f"{row['totalOver']}%", f"{row['totalOverLast5']}%", row["last5"], f"{row['lastTotalOver']}%",overOdds, underOdds])
		reddit += "\n-|-|-|-|-|-|-|-|-|-|-"

	with open(f"{prefix}static/nhlprops/csvs/reddit", "w") as fh:
		fh.write(reddit)

	for prop in csvs:
		with open(f"{prefix}static/nhlprops/csvs/{prop}.csv", "w") as fh:
			fh.write(csvs[prop])

def addNumSuffix(val):
	a = val % 10;
	b = val % 100;
	if val == 0:
		return ""
	if a == 1 and b != 11:
		return f"{val}st"
	elif a == 2 and b != 12:
		return f"{val}nd"
	elif a == 3 and b != 13:
		return f"{val}rd"
	else:
		return f"{val}th"

@nhlprops_blueprint.route('/nhlprops')
def props_route():
	prop = alt = date = teams = ""
	if request.args.get("prop"):
		prop = request.args.get("prop")
	if request.args.get("alt"):
		alt = request.args.get("alt")
	if request.args.get("date"):
		date = request.args.get("date")
	if request.args.get("teams"):
		teams = request.args.get("teams")
	return render_template("nhlprops.html", prop=prop, alt=alt, date=date, teams=teams)

def writeProps(date):
	actionNetworkBookIds = {
		68: "draftkings",
		69: "fanduel"
	}
	
	optionTypes = {}
	propMap = {
		"sog": "core_bet_type_31_shots_on_goal",
		"pts": "core_bet_type_280_points",
	}
	props = {}
	for prop in ["sog", "pts"]:

		path = f"{prefix}static/nhlprops/{prop}.json"
		url = f"https://api.actionnetwork.com/web/v1/leagues/3/props/{propMap[prop]}?bookIds=69,68&date={date.replace('-', '')}"
		time.sleep(0.5)
		os.system(f"curl -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:106.0) Gecko/20100101 Firefox/106.0' -k \"{url}\" -o {path}")

		with open(path) as fh:
			j = json.load(fh)

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
	with open(f"{prefix}static/nhlprops/dates/{date}.json", "w") as fh:
		json.dump(props, fh, indent=4)

def fixLines(props):
	pass

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("-c", "--cron", action="store_true", help="Start Cron Job")
	parser.add_argument("-d", "--date", help="Date")
	parser.add_argument("-w", "--week", help="Week", type=int)

	args = parser.parse_args()

	date = args.date
	if not date:
		date = datetime.now()
		date = str(date)[:10]

	if args.cron:
		writeProps(date)