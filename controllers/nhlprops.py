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

	date = datetime.now()
	date = str(date)[:10]

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
			for teams in schedule[date]:
				teams = teams.split(" @ ")
				if espnTeam in teams:
					if teams.index(espnTeam) == 0:
						opp = teams[1]
					else:
						opp = teams[0]

		if espnTeam.lower() not in ["phx", "lac"]:
			#continue
			pass

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
				if line and avgMin:
					files = sorted(glob.glob(f"{prefix}static/hockeyreference/{espnTeam}/*.json"), key=lambda k: datetime.strptime(k.split("/")[-1].replace(".json", ""), "%Y-%m-%d"), reverse=True)
					for file in files:
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

	write_csvs(props)
	return jsonify(props)

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
	prop = ""
	if request.args.get("prop"):
		prop = request.args.get("prop")
	return render_template("nhlprops.html", prop=prop)

def writeProps(date):
	url = "https://www.actionnetwork.com/nhl/props/shots-on-goal"

	props = {}

	for prop in ["sog", "pts"]:
		path = f"{prefix}static/nhlprops/{prop}.html"
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