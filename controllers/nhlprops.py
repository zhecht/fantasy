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
	with open(f"{prefix}static/hockeyreference/rankings.json") as fh:
		rankings = json.load(fh)
	with open(f"{prefix}static/hockeyreference/totals.json") as fh:
		stats = json.load(fh)
	with open(f"{prefix}static/hockeyreference/scores.json") as fh:
		scores = json.load(fh)
	with open(f"{prefix}static/hockeyreference/averages.json") as fh:
		averages = json.load(fh)
	with open(f"{prefix}static/hockeyreference/lastYearStats.json") as fh:
		lastYearStats = json.load(fh)
	with open(f"{prefix}static/hockeyreference/schedule.json") as fh:
		schedule = json.load(fh)
	with open(f"{prefix}static/nhlprops/lines.json") as fh:
		gameLines = json.load(fh)

	props = []
	for game in propData:
		for player in propData[game]:
			shortFirstName = player.split(" ")[0][0]
			restName = " ".join(player.title().split(" ")[1:])
			name = f"{shortFirstName.upper()}. {restName.replace('-', ' ')}"

			team = opp = ""
			gameSp = game.split(" @ ")
			team1, team2 = gameSp[0], gameSp[1]
			if name in stats[team1]:
				team = team1
				opp = team2
			elif name in stats[team2]:
				team = team2
				opp = team1
			else:
				continue

			if teams and team not in teams:
				continue

			avgMin = 0
			if team in stats and name in stats[team] and stats[team][name]["gamesPlayed"]:
				avgMin = int(stats[team][name]["toi"] / stats[team][name]["gamesPlayed"])

			for prop in propData[game][player]:
				convertedProp = convertProp(prop)
				line = propData[game][player][prop]["line"]
				avg = 0

				if team in stats and name in stats[team] and stats[team][name]["gamesPlayed"]:
					val = 0
					if convertedProp == "pts":
						val = stats[team][name]["g"] + stats[team][name]["a"]
					elif convertedProp in stats[team][name]:
						val = stats[team][name][convertedProp]
					avg = round(val / stats[team][name]["gamesPlayed"], 2)

				overOdds = propData[game][player][prop]["over"]
				underOdds = propData[game][player][prop]["under"]

				lastAvg = lastAvgMin = 0
				proj = 0
				if name in averages[team] and averages[team][name]:
					lastAvgMin = averages[team][name]["toi/g"]
					if convertedProp in averages[team][name]:
						lastAvg = averages[team][name][convertedProp]
					lastAvg = lastAvg / averages[team][name]["gamesPlayed"]
					proj = lastAvg / lastAvgMin
					lastAvg = round(lastAvg, 2)

				diff = diffAvg = 0
				if avg and line:
					diffAvg = round((avg / float(line) - 1), 2)
				if lastAvg and line:
					diff = round((lastAvg / float(line) - 1), 2)

				lastTotalOver = lastTotalGames = 0
				if line and avgMin and name in lastYearStats[team] and lastYearStats[team][name]:
					for d in lastYearStats[team][name]:
						minutes = lastYearStats[team][name][d]["toi/g"]
						if minutes > 0 and convertedProp in lastYearStats[team][name][d]:
							lastTotalGames += 1
							val = lastYearStats[team][name][d][convertedProp]
							valPerMin = float(val / minutes)
							linePerMin = float(line) / avgMin
							if valPerMin > linePerMin:
								lastTotalOver += 1
				if lastTotalGames:
					lastTotalOver = round((lastTotalOver / lastTotalGames) * 100)

				winLossSplits = [[],[]]
				totalOver = totalOverLast5 = totalGames = 0
				last5 = []
				hit = False
				if line and avgMin:
					files = sorted(glob.glob(f"{prefix}static/hockeyreference/{team}/*.json"), key=lambda k: datetime.strptime(k.split("/")[-1].replace(".json", ""), "%Y-%m-%d"), reverse=True)
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

								pastOpp = ""
								for g in schedule[chkDate]:
									gameSp = g.split(" @ ")
									if team in gameSp:
										pastOpp = gameSp[0] if team == gameSp[1] else gameSp[1]
										break

								if chkDate == date:
									if val > float(line):
										hit = True

								if len(last5) < 10:
									v = str(int(val))
									if chkDate == date:
										v = f"'{v}'"
										last5.append(v)
										continue
									last5.append(v)

								teamScore = scores[chkDate][team]
								oppScore = scores[chkDate][pastOpp]
								if teamScore > oppScore:
									winLossSplits[0].append(val)
								elif teamScore < oppScore:
									winLossSplits[1].append(val)

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
					if last5Size:
						totalOverLast5 = round((totalOverLast5 / last5Size) * 100)

				diffAbs = 0
				if avgMin:
					proj = round(proj*float(avgMin), 1)
					if line:
						diffAbs = round((proj / float(line) - 1), 2)
					else:
						diffAbs = diffAvg

				winSplitAvg = lossSplitAvg = 0
				if len(winLossSplits[0]):
					winSplitAvg = round(sum(winLossSplits[0]) / len(winLossSplits[0]),2)
				if len(winLossSplits[1]):
					lossSplitAvg = round(sum(winLossSplits[1]) / len(winLossSplits[1]),2)
				winLoss = f"{winSplitAvg} - {lossSplitAvg}"

				oppOver = oppOverTot = 0
				if prop == "sv":
					files = sorted(glob.glob(f"{prefix}static/hockeyreference/{team}/*.json"))
					for file in files:
						with open(file) as fh:
							gameStats = json.load(fh)
						oppOverTot += 1
						totSaves = 0
						for p in gameStats:
							totSaves += gameStats[p].get("sv", 0)
						if totSaves > float(line):
							oppOver += 1
					oppOver = round(oppOver * 100 / oppOverTot)

				gameLine = ""
				if game in gameLines:
					gameOdds = gameLines[game]["moneyline"]["odds"].split(",")
					if team == game.split(" @ ")[0]:
						gameLine = gameOdds[0]
					else:
						gameLine = gameOdds[1]

				props.append({
					"player": player.title(),
					"team": team.upper(),
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
					"oppOver": oppOver,
					"gameLine": gameLine,
					"winLossSplits": winLoss,
					"ptsPerGame": round((rankings[team]["tot"]["G"] / rankings[team]["tot"]["GP"]) + rankings[team]["tot"]["A/GP"], 1),
					"ptsPerGameLast5": round((rankings[team]["last5"]["G"] / rankings[team]["last5"]["GP"]) + rankings[team]["last5"]["A/GP"], 1),
					"savesPerGame": round(rankings[team]["tot"]["SA/GP"]-rankings[team]["tot"]["GA"]/rankings[team]["tot"]["GP"], 1),
					"savesPerGameLast3": round(rankings[team]["last3"]["SA/GP"]-rankings[team]["last3"]["GA"]/rankings[team]["last3"]["GP"], 1),
					"savesPerGameLast5": round(rankings[team]["last5"]["SA/GP"]-rankings[team]["last5"]["GA"]/rankings[team]["last5"]["GP"], 1),
					"shotsPerGame": round(rankings[team]["tot"]["S/GP"], 1),
					"shotsPerGameLast5": round(rankings[team]["last5"]["S/GP"], 1),
					"shotsAgainstPerGame": round(rankings[team]["tot"]["SA/GP"], 1),
					"shotsAgainstPerGameLast5": round(rankings[team]["last5"]["SA/GP"], 1),
					"oppPtsPerGame": round((rankings[opp]["tot"]["GA"] / rankings[opp]["tot"]["GP"]) + (rankings[opp]["tot"]["OPP A"] / rankings[opp]["tot"]["GP"]), 1),
					"oppPtsPerGameLast5": round((rankings[opp]["last5"]["GA"] / rankings[opp]["last5"]["GP"]) + (rankings[opp]["last5"]["OPP A"] / rankings[opp]["last5"]["GP"]), 1),
					"oppSavesAgainstPerGame": round(rankings[opp]["tot"]["S/GP"]-rankings[opp]["tot"]["G"]/rankings[opp]["tot"]["GP"], 1),
					"oppSavesAgainstPerGameLast3": round(rankings[opp]["last3"]["S/GP"]-rankings[opp]["last3"]["G"]/rankings[opp]["last3"]["GP"], 1),
					"oppSavesAgainstPerGameLast5": round(rankings[opp]["last5"]["S/GP"]-rankings[opp]["last5"]["G"]/rankings[opp]["last5"]["GP"], 1),
					"oppShotsAgainstPerGame": round(rankings[opp]["tot"]["SA/GP"], 1),
					"oppShotsAgainstPerGameLast5": round(rankings[opp]["last5"]["SA/GP"], 1),
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
		if prop in splitProps:
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

def convertDKTeam(team):
	if team == "was":
		return "wsh"
	return team

def writeGameLines(date):
	with open(f"{prefix}static/nhlprops/lines.json") as fh:
		lines = json.load(fh)

	url = "https://sportsbook-us-mi.draftkings.com//sites/US-MI-SB/api/v5/eventgroups/42133?format=json"
	outfile = "out"
	call(["curl", "-k", url, "-o", outfile])

	with open("out") as fh:
		data = json.load(fh)

	events = {}
	lines = {}
	displayTeams = {}
	if "eventGroup" not in data:
		return
	for event in data["eventGroup"]["events"]:
		displayTeams[event["teamName1"].lower()] = event["teamShortName1"].lower()
		displayTeams[event["teamName2"].lower()] = event["teamShortName2"].lower()
		game = convertDKTeam(event["teamShortName1"].lower()) + " @ " + convertDKTeam(event["teamShortName2"].lower())
		if game not in lines:
			lines[game] = {}
		events[event["eventId"]] = game

	for catRow in data["eventGroup"]["offerCategories"]:
		if catRow["name"].lower() != "game lines":
			continue
		for cRow in catRow["offerSubcategoryDescriptors"]:
			if cRow["name"].lower() != "game":
				continue
			for offerRow in cRow["offerSubcategory"]["offers"]:
				for row in offerRow:
					game = events[row["eventId"]]
					gameType = row["label"].lower().split(" ")[-1]

					switchOdds = False
					team1 = ""
					if gameType != "total":
						outcomeTeam1 = row["outcomes"][0]["label"].lower()
						team1 = displayTeams[outcomeTeam1]
						if team1 != game.split(" @ ")[0]:
							switchOdds = True

					odds = [row["outcomes"][0]["oddsAmerican"], row["outcomes"][1]["oddsAmerican"]]
					if switchOdds:
						odds[0], odds[1] = odds[1], odds[0]

					line = row["outcomes"][0].get("line", 0)
					lines[game][gameType] = {
						"line": line,
						"odds": ",".join(odds)
					}

	with open(f"{prefix}static/nhlprops/lines.json", "w") as fh:
		json.dump(lines, fh, indent=4)


def writeGoalieProps(date):

	url = "https://sportsbook-us-mi.draftkings.com//sites/US-MI-SB/api/v5/eventgroups/42133/categories/1064?format=json"
	outfile = "out"
	call(["curl", "-k", url, "-o", outfile])

	with open("out") as fh:
		data = json.load(fh)

	with open(f"{prefix}static/nhlprops/dates/{date}.json") as fh:
		props = json.load(fh)

	events = {}
	
	prop = "sv"
	if "eventGroup" not in data:
		return
	for event in data["eventGroup"]["events"]:
		if "teamShortName1" not in event:
			game = convertDKTeam(event["teamName1"].lower()) + " @ " + convertDKTeam(event["teamName2"].lower())
		else:
			game = convertDKTeam(event["teamShortName1"].lower()) + " @ " + convertDKTeam(event["teamShortName2"].lower())
		if game not in props:
			props[game] = {}
		events[event["eventId"]] = game

	for catRow in data["eventGroup"]["offerCategories"]:
		if not catRow["name"].lower() == "goalie props":
			continue
		for cRow in catRow["offerSubcategoryDescriptors"]:
			if cRow["name"].lower() != "saves":
				continue
			for offerRow in cRow["offerSubcategory"]["offers"]:
				for row in offerRow:
					game = events[row["eventId"]]
					player = " ".join(row["label"].lower().replace(".", "").replace("'", "").split(" ")[:-1])
					odds = ["",""]
					line = row["outcomes"][0]["line"]
					for outcome in row["outcomes"]:
						if outcome["label"].lower() == "over":
							odds[0] = outcome["oddsAmerican"]
						else:
							odds[1] = outcome["oddsAmerican"]

					if player not in props[game]:
						props[game][player] = {}
					if prop not in props[game][player]:
						props[game][player][prop] = {}
					props[game][player][prop] = {
						"line": line,
						"over": odds[0],
						"under": odds[1]
					}
	with open(f"{prefix}static/nhlprops/dates/{date}.json", "w") as fh:
		json.dump(props, fh, indent=4)

def writeProps(date):
	propNames = ["sog", "pts", "ast"]
	catIds = [1189,550,550]
	subCatIds = [12040,5586,5587]
	props = {}
	for catId, subCatId, prop in zip(catIds, subCatIds, propNames):
		time.sleep(0.5)
		outfile = "out2"
		url = f"https://sportsbook-us-mi.draftkings.com//sites/US-MI-SB/api/v5/eventgroups/42133/categories/{catId}/subcategories/{subCatId}?format=json"
		call(["curl", "-k", url, "-o", outfile])

		with open(outfile) as fh:
			data = json.load(fh)

		events = {}
		if "eventGroup" not in data:
			continue
		for event in data["eventGroup"]["events"]:
			if "teamShortName1" not in event:
				game = convertDKTeam(event["teamName1"].lower()) + " @ " + convertDKTeam(event["teamName2"].lower())
			else:
				game = convertDKTeam(event["teamShortName1"].lower()) + " @ " + convertDKTeam(event["teamShortName2"].lower())
			if game not in props:
				props[game] = {}
			events[event["eventId"]] = game

		for catRow in data["eventGroup"]["offerCategories"]:
			if catRow["offerCategoryId"] != catId:
				continue
			for cRow in catRow["offerSubcategoryDescriptors"]:
				if cRow["subcategoryId"] != subCatId:
					continue
				for offerRow in cRow["offerSubcategory"]["offers"]:
					for row in offerRow:
						game = events[row["eventId"]]
						odds = ["",""]
						line = row["outcomes"][0]["line"]
						player = ""
						for outcome in row["outcomes"]:
							if outcome["label"].lower() == "over":
								odds[0] = outcome["oddsAmerican"]
								player = outcome["participant"].lower().replace(".", "").replace("'", "")
							else:
								odds[1] = outcome["oddsAmerican"]

						if player not in props[game]:
							props[game][player] = {}
						if prop not in props[game][player]:
							props[game][player][prop] = {}
						props[game][player][prop] = {
							"line": line,
							"over": odds[0],
							"under": odds[1]
						}

	with open(f"{prefix}static/nhlprops/dates/{date}.json", "w") as fh:
		json.dump(props, fh, indent=4)

def goalieLines(props):
	with open(f"{prefix}static/nhlprops/goalieProps.json") as fh:
		goalieProps = json.load(fh)

	for game in goalieProps:
		if game not in props:
			props[game] = {}
		for player in goalieProps[game]:
			props[game][player] = {
				"sv": {
					"line": goalieProps[game][player]["sv"]["line"],
					"over": goalieProps[game][player]["sv"]["over"],
					"under": goalieProps[game][player]["sv"]["under"],
				}
			}
	pass

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("-c", "--cron", action="store_true", help="Start Cron Job")
	parser.add_argument("--lines", action="store_true", help="Game Lines")
	parser.add_argument("-d", "--date", help="Date")
	parser.add_argument("-w", "--week", help="Week", type=int)

	args = parser.parse_args()

	date = args.date
	if not date:
		date = datetime.now()
		date = str(date)[:10]

	if args.lines:
		writeGameLines(date)
	elif args.cron:
		writeProps(date)
		writeGoalieProps(date)
		#writeGameLines(date)