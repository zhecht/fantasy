#from selenium import webdriver
from flask import *
from subprocess import call
from bs4 import BeautifulSoup as BS
from sys import platform
from datetime import datetime
from datetime import timedelta

from itertools import zip_longest
import argparse
import time
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
					idx = game.split(" @ ").index(team)
					if idx >= 0:
						opp = game.split(" @ ")[idx]
			if team not in totals:
				totals[team] = {"ppg": 0, "ppga": 0, "games": 0, "overs": [], "ttOvers": []}
			if opp not in totals:
				totals[opp] = {"ppg": 0, "ppga": 0, "games": 0, "overs": [], "ttOvers": []}
			totals[team]["games"] += 1
			totals[team]["ppg"] += scores[date][team]
			totals[team]["ppga"] += scores[date][opp]
			totals[team]["ttOvers"].append(str(scores[date][team]))
			totals[team]["overs"].append(str(scores[date][team] + scores[date][opp]))

	headers = ["team", "ppg", "ppga", "overs", "overs avg", "tt overs", "tt avg", "tt even %"]
	out = "\t".join([x.upper() for x in headers])
	out += "\n"
	#out += ":--|:--|:--|:--|:--|:--|:--\n"
	cutoff = 7
	for game in schedule[today]:
		away, home = map(str, game.split(" @ "))
		ppg = round(totals[away]["ppg"] / totals[away]["games"], 1)
		ppga = round(totals[away]["ppga"] / totals[away]["games"], 1)
		overs = ",".join(totals[away]["overs"][:cutoff])
		oversAvg = round(sum([int(x) for x in totals[away]["overs"]]) / len(totals[away]["overs"]), 1)
		ttOvers = ",".join(totals[away]["ttOvers"][:cutoff])
		ttOversAvg = round(sum([int(x) for x in totals[away]["ttOvers"]]) / len(totals[away]["ttOvers"]), 1)
		ttEven = round(len([x for x in totals[away]["ttOvers"] if int(x) % 2 == 0]) * 100 / len(totals[away]["ttOvers"]), 1)
		out += "\t".join([str(x) for x in [away.upper(), ppg, ppga, overs, oversAvg, ttOvers, ttOversAvg, ttEven]]) + "\n"
		ppg = round(totals[home]["ppg"] / totals[home]["games"], 1)
		ppga = round(totals[home]["ppga"] / totals[home]["games"], 1)
		overs = ",".join(totals[home]["overs"][:cutoff])
		oversAvg = round(sum([int(x) for x in totals[home]["overs"]]) / len(totals[home]["overs"]), 1)
		ttOvers = ",".join(totals[home]["ttOvers"][:cutoff])
		ttOversAvg = round(sum([int(x) for x in totals[home]["ttOvers"]]) / len(totals[home]["ttOvers"]), 1)
		ttEven = round(len([x for x in totals[home]["ttOvers"] if int(x) % 2 == 0]) * 100 / len(totals[home]["ttOvers"]), 1)
		out += "\t".join([str(x) for x in [home.upper(), ppg, ppga, overs, oversAvg, ttOvers, ttOversAvg, ttEven]]) + "\n"
		out += "\t".join(["-"]*len(headers)) + "\n"

	with open(f"{prefix}static/nbaprops/csvs/totals.csv", "w") as fh:
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

def convertRotoPlayer(player):
	trans = {
		"nicolas claxton": "nic claxton",
		"jaren jackson": "jaren jackson jr",
		"michael porter": "michael porter jr",
		"marvin bagley": "marvin bagley iii",
		"lonnie walker": "lonnie walker iv",
		"troy brown": "troy brown jr",
		"danuel house": "danuel house jr",
		"otto porter": "otto porter jr",
		"kevin porter": "kevin porter jr",
		"jabari smith": "jabari smith jr",
		"gary trent": "gary trent jr",
		"marcus morris": "marcus morris sr",
		"wendell carter": "wendell carter jr",
	}
	return trans.get(player, player)

def writeLineups():

	with open(f"{prefix}static/basketballreference/totals.json") as fh:
		stats = json.load(fh)
	with open(f"{prefix}static/basketballreference/schedule.json") as fh:
		schedule = json.load(fh)

	url = "https://www.rotowire.com/basketball/nba-lineups.php"
	outfile = "out"
	call(["curl", "-k", url, "-o", outfile])
	soup = BS(open(outfile, 'rb').read(), "lxml")

	date = datetime.now()
	date = str(date)[:10]

	lineups = {}
	for game in soup.findAll("div", class_="lineup"):
		if "is-tools" in game.get("class"):
			continue
		teams = game.findAll("a", class_="lineup__team")
		lineupList = game.findAll("ul", class_="lineup__list")
		for idx, teamLink in enumerate(teams):
			team = teamLink.get("href").split("-")[-1]
			if team == "was":
				team = "wsh"
			elif team == "nop":
				team = "no"
			elif team == "sas":
				team = "sa"
			elif team == "uta":
				team = "utah"
			elif team == "gsw":
				team = "gs"
			elif team == "nyk":
				team = "ny"
			lineups[team] = {
				"starters": {},
				"injuries": {}
			}
			injured = False

			for playerIdx, li in enumerate(lineupList[idx].findAll("li", class_="lineup__player")):
				player = " ".join(li.find("a").get("href").split("/")[-1].split("-")[:-1])
				player = convertRotoPlayer(player)
				pos = li.find("div").text
				inj = "-"
				if li.find("span"):
					inj = li.find("span").text

				avgMin = ppg = apg = rpg = 0
				if player in stats[team] and stats[team][player]["gamesPlayed"]:
					gamesPlayed = stats[team][player]["gamesPlayed"]
					avgMin = int(stats[team][player]["min"] / gamesPlayed)
					ppg = round(stats[team][player]["pts"] / gamesPlayed, 1)
					apg = round(stats[team][player]["ast"] / gamesPlayed, 1)
					rpg = round(stats[team][player]["reb"] / gamesPlayed, 1)
				j = {
					"pos": pos,
					"inj": inj,
					"avgMin": avgMin,
					"ppg": ppg,
					"apg": apg,
					"rpg": rpg
				}

				if playerIdx >= 5 and "has-injury-status" in li.get("class"):
					lineups[team]["injuries"][player] = j
				else:
					lineups[team]["starters"][player] = j

	with open(f"{prefix}static/nbaprops/lineups.json", "w") as fh:
		json.dump(lineups, fh, indent=4)

	headers = ["NAME","TEAM","POS","INJ","MIN","RPG","APG","PPG"]
	out = "\t".join(headers+[" "]+headers) + "\n"
	for game in schedule[date]:
		away, home = map(str, game.split(" @ "))
		for starting in ["starters", "injuries"]:
			out += f"{away.upper()} {starting.capitalize()}\t"
			out += "\t".join(["-"]*len(headers))
			out += f"\t{home.upper()} {starting.capitalize()}\t"
			out += "\t".join(["-"]*(len(headers)-1)) + "\n"
			zip1 = lineups[away][starting]
			zip2 = lineups[home][starting]
			for awayPlayer, homePlayer in zip_longest(zip1, zip2):
				if awayPlayer:
					awayData = lineups[away][starting][awayPlayer]
					out += "\t".join([awayPlayer.title(), away.upper(), awayData["pos"], awayData["inj"], str(awayData["avgMin"]), str(awayData["rpg"]), str(awayData["apg"]), str(awayData["ppg"])])
				else:
					out += "\t".join(["-"]*(len(headers)))

				out += "\t\t"
				if homePlayer:
					homeData = lineups[home][starting][homePlayer]
					out += "\t".join([homePlayer.title(), home.upper(), homeData["pos"], homeData["inj"], str(homeData["avgMin"]), str(homeData["rpg"]), str(homeData["apg"]), str(homeData["ppg"])])
				else:
					out += "\t".join(["-"]*(len(headers)))
				out += "\n"
			out += "\t".join(["-"]*(len(headers)*2+1)) + "\n"
		out += "\t".join(["-"]*(len(headers)*2+1)) + "\n"
		out += "\t".join(["-"]*(len(headers)*2+1)) + "\n"

	with open(f"{prefix}static/nbaprops/csvs/lineups.csv", "w") as fh:
		fh.write(out)

def writeProps(date):
	ids = {
		"pts": [1215, 12488],
		"reb": [1216, 12492],
		"ast": [1217, 12495],
		"pts+reb+ast": [583, 5001],
		"pts+reb": [583, 9976],
		"pts+ast": [583, 9973],
		"reb+ast": [583, 9974],
		"stl+blk": [1219, 12502],
		"3ptm": [1218, 12497],
		"blk": [1219, 12499],
		"stl": [1219, 12500],
		"to": [1220, 12504]
	}

	props = {}
	if os.path.exists(f"{prefix}static/nbaprops/dates/{date}.json"):
		with open(f"{prefix}static/nbaprops/dates/{date}.json") as fh:
			props = json.load(fh)

	for prop in ids:
		time.sleep(0.5)
		url = f"https://sportsbook-us-mi.draftkings.com//sites/US-MI-SB/api/v5/eventgroups/42648/categories/{ids[prop][0]}/subcategories/{ids[prop][1]}?format=json"
		outfile = "out"
		call(["curl", "-k", url, "-o", outfile])

		with open("out") as fh:
			data = json.load(fh)

		events = {}
		if "eventGroup" not in data:
			continue
		for event in data["eventGroup"]["events"]:
			start = f"{event['startDate'].split('T')[0]}T{':'.join(event['startDate'].split('T')[1].split(':')[:2])}Z"
			startDt = datetime.strptime(start, "%Y-%m-%dT%H:%MZ") - timedelta(hours=5)
			if startDt.day != int(date[-2:]):
				continue
				pass
			if "teamShortName1" not in event:
				game = convertDKTeam(event["teamName1"].lower()) + " @ " + convertDKTeam(event["teamName2"].lower())
			else:
				game = convertDKTeam(event["teamShortName1"].lower()) + " @ " + convertDKTeam(event["teamShortName2"].lower())
			if game not in props:
				props[game] = {}
			events[event["eventId"]] = game

		for catRow in data["eventGroup"]["offerCategories"]:
			if catRow["offerCategoryId"] != ids[prop][0]:
				continue
			for cRow in catRow["offerSubcategoryDescriptors"]:
				if cRow["subcategoryId"] != ids[prop][1]:
					continue
				for offerRow in cRow["offerSubcategory"]["offers"]:
					for row in offerRow:
						try:
							game = events[row["eventId"]]
						except:
							continue
						try:
							player = row["outcomes"][0]["participant"].lower().replace(".", "").replace("'", "").replace("-", " ")
						except:
							continue
						if player == "nicolas claxton":
							player = "nic claxton"
						elif player == "marvin bagley":
							player = "marvin bagley iii"
						elif player == "jabari smith":
							player = "jabari smith jr"
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

	with open(f"{prefix}static/nbaprops/dates/{date}.json", "w") as fh:
		json.dump(props, fh, indent=4)

def getOppOvers(schedule, roster):
	overs = {}
	for team in roster:
		files = sorted(glob.glob(f"{prefix}static/basketballreference/{team}/*.json"), key=lambda k: datetime.strptime(k.split("/")[-1].replace(".json", ""), "%Y-%m-%d"), reverse=True)
		for file in files:
			chkDate = file.split("/")[-1].replace(".json","")
			opp = ""
			for game in schedule[chkDate]:
				if team in game.split(" @ "):
					opp = [t for t in game.split(" @ ") if t != team][0]
			if opp not in overs:
				overs[opp] = {}

			with open(file) as fh:
				gameStats = json.load(fh)
			for player in gameStats:
				if player not in roster[team] or gameStats[player]["min"] < 25:
					continue

				pos = roster[team][player]
				if pos == "G":
					pos = "SG"
				elif pos == "F":
					pos = "PF"
				if pos not in overs[opp]:
					overs[opp][pos] = {}
				for prop in ["pts", "ast", "reb", "blk", "stl", "pts+ast", "pts+reb", "pts+reb+ast", "reb+ast", "stl+blk", "3ptm"]:
					if prop not in overs[opp][pos]:
						overs[opp][pos][prop] = []
					if "+" in prop or prop in gameStats[player]:
						val = 0.0
						if "+" in prop:
							for p in prop.split("+"):
								val += gameStats[player][p]
						else:
							val = gameStats[player][prop]
						val = val / gameStats[player]["min"]
						overs[opp][pos][prop].append(val)
	return overs


@nbaprops_blueprint.route('/getNBAProps')
def getProps_route():
	res = []

	teamsArg = request.args.get("teams") or ""
	if teamsArg:
		teamsArg = teamsArg.lower().split(",")
	alt = request.args.get("alt") or ""
	playersArg = request.args.get("players") or []
	if playersArg:
		playersArg = playersArg.split(",")

	date = datetime.now()
	date = str(date)[:10]
	if request.args.get("date"):
		date = request.args.get("date")

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
	with open(f"{prefix}static/basketballreference/scores.json") as fh:
		scores = json.load(fh)
	with open(f"{prefix}static/nbaprops/lines/{date}.json") as fh:
		gameLines = json.load(fh)

	oppOvers = getOppOvers(schedule, roster)
	#propData = customPropData(propData)

	props = []
	for game in propData:
		for propName in propData[game]:
			name = propName

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
				print(game, name)
				continue

			if teamsArg and team not in teamsArg:
				continue

			if playersArg and name not in playersArg:
				continue

			avgMin = 0
			if team in stats and name in stats[team] and stats[team][name]["gamesPlayed"]:
				avgMin = int(stats[team][name]["min"] / stats[team][name]["gamesPlayed"])
			for prop in propData[game][propName]:

				if prop == "to" or "-1q" in prop:
					continue

				line = propData[game][propName][prop]["line"]
				avg = "-"

				if "+" in prop:
					#continue
					pass
				if prop in ["stl", "blk", "stl+blk", "3ptm"]:
					#continue
					pass

				if team in stats and name in stats[team] and stats[team][name]["gamesPlayed"]:
					val = 0
					if "+" in prop:
						for p in prop.split("+"):
							val += stats[team][name][p]
					elif prop in stats[team][name]:
						val = stats[team][name][prop]
					avg = round(val / stats[team][name]["gamesPlayed"], 1)

				overOdds = propData[game][propName][prop]["over"]
				underOdds = propData[game][propName][prop]["under"]

				try:
					line = float(line)
				except:
					line = 0.0

				if alt and line:
					if prop in ["stl+blk", "reb+ast"]:
						continue
					if prop not in ["reb", "ast"]:
						#continue
						pass
					if alt == "maxover":
						if prop not in ["reb", "ast"]:
							continue
						if "pts+" in prop:
							line = math.floor(line / 5)*5 - 0.5
							continue
						elif line > 5:
							line -= 2
						else:
							line -= 1
					elif alt == "over":
						if "+" in prop or prop in ["3ptm", "stl", "blk"]:
							pass
							continue
						if "pts+" in prop:
							line = math.floor(line / 5)*5 - 0.5
						elif line > 5:
							line -= 1
						else:
							if overOdds > -140:
								line -= 1
					else:
						if prop not in ["reb", "ast"]:
							continue
						if line > 5:
							line += 1
						else:
							line += 1
					if line < 0:
						line = 0

				lastAvg = lastAvgMin = 0
				proj = 0
				if name in averages[team] and averages[team][name]:
					lastAvgMin = averages[team][name]["min"]
					if "+" in prop:
						for p in prop.split("+"):
							lastAvg += averages[team][name][p]
					elif prop in averages[team][name]:
						lastAvg = averages[team][name][prop]
					proj = lastAvg / lastAvgMin
					lastAvg = round(lastAvg, 1)

				diff = diffAvg = 0
				if avg != "-" and line:
					diffAvg = round((avg / float(line) - 1), 2)
				if lastAvg and line:
					diff = round((lastAvg / float(line) - 1), 2)

				lastTotalOver = lastTotalGames = 0
				if line and avgMin and name in lastYearStats[team] and lastYearStats[team][name]:
					for dt in lastYearStats[team][name]:
						minutes = lastYearStats[team][name][dt]["min"]
						if minutes > 0:
							lastTotalGames += 1
							if "+" in prop:
								val = 0.0
								for p in prop.split("+"):
									val += lastYearStats[team][name][dt][p]
							else:
								val = lastYearStats[team][name][dt][prop]
							valPerMin = float(val / minutes)
							linePerMin = float(line) / avgMin
							if valPerMin > linePerMin:
								lastTotalOver += 1
				if lastTotalGames:
					lastTotalOver = round((lastTotalOver / lastTotalGames) * 100)

				totalOverPerMin = totalOver = totalOverLast5 = totalGames = avgVariance = 0
				last5 = []
				lastAll = []
				lastAllPerMin = []
				winLossSplits = [[],[]]
				awayHomeSplits = [[],[]]
				hit = False
				if line and avgMin:
					files = sorted(glob.glob(f"{prefix}static/basketballreference/{team}/*.json"), key=lambda k: datetime.strptime(k.split("/")[-1].replace(".json", ""), "%Y-%m-%d"), reverse=True)
					for file in files:
						chkDate = file.split("/")[-1].replace(".json","")
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

								pastOpp = ""
								teamIsAway = False
								for g in schedule[chkDate]:
									gameSp = g.split(" @ ")
									if team in gameSp:
										if team == gameSp[0]:
											teamIsAway = True
											pastOpp = gameSp[1]
										else:
											pastOpp = gameSp[0]
										break

								if chkDate == date:
									if alt.endswith("over") and val > float(line):
										hit = True
									elif alt == "under" and val < float(line):
										hit = True
									elif not alt and val > float(line):
										hit = True

								avgVariance += (val / float(line)) - 1
								if len(last5) < 7:
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

								if teamIsAway:
									awayHomeSplits[0].append(val)
								else:
									awayHomeSplits[1].append(val)

								valPerMin = float(val / minutes)
								linePerMin = float(line) / avgMin
								lastAll.append(str(int(val)))
								lastAllPerMin.append(str(valPerMin))
								if valPerMin > linePerMin:
									totalOverPerMin += 1
								if val > float(line):
									totalOver += 1
									if len(last5) <= 5:
										totalOverLast5 += 1
				if totalGames:
					totalOver = round((totalOver / totalGames) * 100)
					totalOverPerMin = round((totalOverPerMin / totalGames) * 100)
					avgVariance = round(avgVariance / totalGames, 2)
					last5Size = len(last5) if len(last5) < 5 else 5
					totalOverLast5 = round((totalOverLast5 / last5Size) * 100)

				diffAbs = 0
				if avgMin:
					proj = round(proj*float(avgMin), 1)
					if line:
						diffAbs = round((proj / float(line) - 1), 2)
					else:
						diffAbs = diffAvg

				pos = roster[team][name]

				oppRank = ""
				rankingsPos = pos
				if pos == "F":
					rankingsPos = "PF"
				elif pos == "G":
					rankingsPos = "SG"
				if rankingsPos in rankings[opp] and prop in rankings[opp][rankingsPos]:
					oppRank = rankings[opp][rankingsPos][prop+"_rank"]

				oppOver = 0
				overPos = pos
				if pos == "G":
					overPos = "SG"
				elif pos == "F":
					overPos = "PF"
				overList = oppOvers[opp][overPos][prop]
				linePerMin = 0
				if avgMin:
					linePerMin = line / avgMin
				if overList:
					oppOver = round(len([x for x in overList if x > linePerMin]) * 100 / len(overList))

				if not line:
					continue

				gameLine = 0
				if game in gameLines:
					gameOdds = gameLines[game]["moneyline"]["odds"].split(",")
					if team == game.split(" @ ")[0]:
						gameLine = gameOdds[0]
					else:
						gameLine = gameOdds[1]

				winSplitAvg = lossSplitAvg = 0
				if len(winLossSplits[0]):
					winSplitAvg = round(sum(winLossSplits[0]) / len(winLossSplits[0]),2)
				if len(winLossSplits[1]):
					lossSplitAvg = round(sum(winLossSplits[1]) / len(winLossSplits[1]),2)
				winLossSplits = f"{winSplitAvg} - {lossSplitAvg}"

				awaySplitAvg = homeSplitAvg = 0
				if len(awayHomeSplits[0]):
					awaySplitAvg = round(sum(awayHomeSplits[0]) / len(awayHomeSplits[0]),2)
				if len(awayHomeSplits[1]):
					homeSplitAvg = round(sum(awayHomeSplits[1]) / len(awayHomeSplits[1]),2)
				awayHomeSplits = f"{awaySplitAvg} - {homeSplitAvg}"

				props.append({
					"game": game,
					"player": name.title(),
					"team": team.upper(),
					"opponent": opp,
					"hit": hit,
					"gameLine": gameLine,
					"awayHome": "A" if team == game.split(" @ ")[0] else "H",
					"awayHomeSplits": awayHomeSplits,
					"winLossSplits": winLossSplits,
					"position": pos,
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
					"oppRank": oppRank,
					"oppOver": oppOver,
					"lastAvgMin": lastAvgMin,
					"totalOver": totalOver,
					"totalOverPerMin": totalOverPerMin,
					"totalOverLast5": totalOverLast5,
					"lastTotalOver": lastTotalOver,
					"last5": ",".join(last5),
					"lastAll": ",".join(lastAll),
					"lastAllPerMin": ",".join(lastAllPerMin),
					"overOdds": overOdds,
					"underOdds": underOdds
				})

	if not alt and not playersArg:
		teamTotals(date, schedule)
		write_csvs(props)
	return jsonify(props)

def h2h(props):
	with open(f"{prefix}static/nbaprops/h2h.json") as fh:
		h2h = json.load(fh)

	out = ""
	for game in h2h:
		out += "\n"+game.upper()+"\n"
		for prop in h2h[game]:
			tabLen = 1
			out += "\t"*tabLen+prop+"\n"
			tabLen += 1

			for matchup in h2h[game][prop]:
				odds = h2h[game][prop][matchup].split(",")
				arrs = []
				players = matchup.split(" v ")
				arrs = [p for p in props if p["player"].lower() in players and p["propType"] == prop]
				if len(arrs) < 2:
					#print(arrs)
					continue

				if players[0] != arrs[0]["player"].lower():
					arrs[0], arrs[1] = arrs[1], arrs[0]

				straightOver = straightTotal = 0
				for num1, num2 in zip(arrs[0]["lastAll"].split(","), arrs[1]["lastAll"].split(",")):
					if int(num1) == int(num2):
						continue
					elif int(num1) > int(num2):
						straightOver += 1
					straightTotal += 1
				if straightTotal:
					straightOver = round(straightOver * 100 / straightTotal)

				allPairsOver = allPairsTotal = allPairsOdds = 0
				for num1 in arrs[0]["lastAll"].split(","):
					for num2 in arrs[1]["lastAll"].split(","):
						if int(num1) == int(num2):
							continue
						elif int(num1) > int(num2):
							allPairsOver += 1
						allPairsTotal += 1
				if allPairsTotal:
					allPairsOver = round(allPairsOver * 100 / allPairsTotal)
					allPairsOdds = (100*allPairsOver) / (-100+allPairsOver)

				straightOverPerMin = straightTotalPerMin = 0
				for num1, num2 in zip(arrs[0]["lastAllPerMin"].split(","), arrs[1]["lastAllPerMin"].split(",")):
					if float(num1) == float(num2):
						continue
					elif float(num1) > float(num2):
						straightOverPerMin += 1
					straightTotalPerMin += 1
				if straightTotalPerMin:
					straightOverPerMin = round(straightOverPerMin * 100 / straightTotalPerMin)

				allPairsOverPerMin = allPairsTotalPerMin = 0
				for num1 in arrs[0]["lastAllPerMin"].split(","):
					for num2 in arrs[1]["lastAllPerMin"].split(","):
						if float(num1) == float(num2):
							continue
						elif float(num1) > float(num2):
							allPairsOverPerMin += 1
						allPairsTotalPerMin += 1
				if allPairsTotalPerMin:
					allPairsOverPerMin = round(allPairsOverPerMin * 100 / allPairsTotalPerMin)

				out += "\t"*tabLen+f"Straight up: {straightOver}% / PM: {straightOverPerMin}%\n"
				out += "\t"*tabLen+f"All Pairs: {allPairsOver}% / PM: {allPairsOverPerMin}%\n"
				data = arrs[0]
				for player, odds in zip(players, odds):
					out += "\t"*tabLen+f"{player.title()} {data['line']}{prop} ({odds}):\n"
					out += "\t"*(tabLen+1)+f"{data['lastAll']}\n"
					data = arrs[1]
				out += "\t"*tabLen+"-----\n"



	with open(f"{prefix}static/nbaprops/h2h.txt", "w") as fh:
		fh.write(out)

def write_csvs(props):
	csvs = {}
	splitProps = {"full": []}
	headers = "\t".join(["NAME","POS","AVG MIN","ML","A/H","TEAM","OPP","OPP RANK","PROP","LINE","SZN AVG","W-L Splits","A-H Splits","% OVER","L5 % OVER","LAST 7 GAMES ➡️","LAST YR % OVER","OVER", "UNDER"])
	reddit = "|".join(headers.split("\t"))
	reddit += "\n:--|:--|:--|:--|:--|:--|:--|:--|:--|:--|:--|:--|:--|:--|:--|:--|:--|:--|:--"

	for row in props:
		if row["propType"] not in splitProps:
			splitProps[row["propType"]] = []
		splitProps[row["propType"]].append(row)
		splitProps["full"].append(row)

	for prop in splitProps:
		csvs[prop] = headers
		rows = sorted(splitProps[prop], key=lambda k: (k["totalOverLast5"], k["totalOver"]), reverse=True)
		for row in rows:
			overOdds = row["overOdds"]
			underOdds = row["underOdds"]
			gameLine = row["gameLine"]
			if underOdds == '-inf':
				underOdds = 0
			if int(overOdds) > 0:
				overOdds = "'"+overOdds
			if int(underOdds) > 0:
				underOdds = "'"+underOdds
			if int(gameLine) > 0:
				gameLine = "'"+gameLine
			try:
				csvs[prop] += "\n" + "\t".join([row["player"], row["position"], str(row["avgMin"]), gameLine, row["awayHome"], row["team"], row["opponent"].upper(), addNumSuffix(row["oppRank"]), row["propType"], str(row["line"]), str(row["avg"]), row["winLossSplits"], row["awayHomeSplits"], f"{row['totalOver']}%", f"{row['totalOverLast5']}%", row["last5"], f"{row['lastTotalOver']}%",overOdds, underOdds])
			except:
				pass

	# add full rows
	csvs["full_name"] = headers
	rows = sorted(splitProps["full"], key=lambda k: (k["player"], -k["totalOverLast5"], -k["totalOver"]))
	for row in rows:
		overOdds = row["overOdds"]
		underOdds = row["underOdds"]
		gameLine = row["gameLine"]
		if underOdds == '-inf':
			underOdds = 0
		if int(overOdds) > 0:
			overOdds = "'"+overOdds
		if int(underOdds) > 0:
			underOdds = "'"+underOdds
		if int(gameLine) > 0:
			gameLine = "'"+gameLine
		try:
			csvs["full_name"] += "\n" + "\t".join([row["player"], row["position"], str(row["avgMin"]), gameLine, row["awayHome"], row["team"], row["opponent"].upper(), addNumSuffix(row["oppRank"]), row["propType"], str(row["line"]), str(row["avg"]), row["winLossSplits"], row["awayHomeSplits"], f"{row['totalOver']}%", f"{row['totalOverLast5']}%", row["last5"], f"{row['lastTotalOver']}%",overOdds, underOdds])
		except:
			pass

	csvs["full_hit"] = headers
	rows = sorted(splitProps["full"], key=lambda k: (k["totalOverLast5"], k["totalOver"]), reverse=True)
	for row in rows:
		overOdds = row["overOdds"]
		underOdds = row["underOdds"]
		gameLine = row["gameLine"]
		if underOdds == '-inf':
			underOdds = 0
		if int(overOdds) > 0:
			overOdds = "'"+overOdds
		if int(underOdds) > 0:
			underOdds = "'"+underOdds
		if int(gameLine) > 0:
			gameLine = "'"+gameLine
		try:
			csvs["full_hit"] += "\n" + "\t".join([row["player"], row["position"], str(row["avgMin"]), gameLine, row["awayHome"], row["team"], row["opponent"].upper(), addNumSuffix(row["oppRank"]), row["propType"], str(row["line"]), str(row["avg"]), row["winLossSplits"], row["awayHomeSplits"], f"{row['totalOver']}%", f"{row['totalOverLast5']}%", row["last5"], f"{row['lastTotalOver']}%",overOdds, underOdds])
		except:
			pass

	# add top 4 to reddit
	for prop in ["pts", "reb", "ast"]:
		rows = sorted(splitProps[prop], key=lambda k: (k["totalOverLast5"], k["totalOver"]), reverse=True)
		for row in rows[:3]:
			overOdds = row["overOdds"]
			underOdds = row["underOdds"]
			gameLine = int(row["gameLine"])
			avg = row["avg"]
			if avg >= row["line"]:
				avg = f"**{avg}**"
			winLossSplits = row["winLossSplits"].split(" - ")
			if float(winLossSplits[0]) >= row["line"]:
				winLossSplits[0] = f"**{winLossSplits[0]}**"
			if float(winLossSplits[1]) >= row["line"]:
				winLossSplits[1] = f"**{winLossSplits[1]}**"
			if gameLine < 0:
				winLossSplits[0] = f"'{winLossSplits[0]}'"
			else:
				winLossSplits[1] = f"'{winLossSplits[1]}'"
			winLossSplits = " - ".join(winLossSplits)
			awayHomeSplits = row["awayHomeSplits"].split(" - ")
			if float(awayHomeSplits[0]) >= row["line"]:
				awayHomeSplits[0] = f"**{awayHomeSplits[0]}**"
			if float(awayHomeSplits[1]) >= row["line"]:
				awayHomeSplits[1] = f"**{awayHomeSplits[1]}**"
			if row["awayHome"] == "A":
				awayHomeSplits[0] = f"'{awayHomeSplits[0]}'"
			else:
				awayHomeSplits[1] = f"'{awayHomeSplits[1]}'"
			awayHomeSplits = " - ".join(awayHomeSplits)
			try:
				reddit += "\n" + "|".join([str(x) for x in [row["player"], row["position"], row["avgMin"], row["gameLine"], row["awayHome"], row["team"], row["opponent"].upper(), addNumSuffix(row["oppRank"]), row["propType"], row["line"], avg, winLossSplits, awayHomeSplits, f"{row['totalOver']}%", f"{row['totalOverLast5']}%", row["last5"], f"{row['lastTotalOver']}%",overOdds, underOdds]])
			except:
				pass
		reddit += "\n-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-|-"

	with open(f"{prefix}static/nbaprops/csvs/reddit", "w") as fh:
		fh.write(reddit)

	for prop in csvs:
		if prop == "full":
			continue
		with open(f"{prefix}static/nbaprops/csvs/{prop}.csv", "w") as fh:
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

def convertRankingsProp(prop):
	if "+" in prop:
		return prop
	elif prop == "3ptm":
		return "3pt%"
	elif prop in ["blk", "stl"]:
		return prop+"pg"
	elif prop in ["pts", "fgm"]:
		return "fgpg"
	return prop[0]+"pg"

def zeroProps():
	with open(f"{prefix}static/nbaprops/customProps.json") as fh:
		data = json.load(fh)
	for team in data:
		for player in data[team]:
			for prop in data[team][player]:
				data[team][player][prop]["odds"] = ["-0"]*len(data[team][player][prop]["odds"])
	with open(f"{prefix}static/nbaprops/customProps.json", "w") as fh:
		json.dump(data, fh, indent=4)

def convertDKTeam(team):
	if team.startswith("was"):
		return "wsh"
	elif team.startswith("pho"):
		return "phx"
	elif team.startswith("uta"):
		return "utah"
	elif team.startswith("sas"):
		return "sa"
	elif team.startswith("nyk"):
		return "ny"
	elif team.startswith("la lakers"):
		return "lal"
	elif team.startswith("la clippers"):
		return "lac"
	return team.split(" ")[0]

def writeTeamProps():
	url = f"https://sportsbook-us-mi.draftkings.com//sites/US-MI-SB/api/v5/eventgroups/42648/categories/523?format=json"
	outfile = "out"
	call(["curl", "-k", url, "-o", outfile])

	with open("out") as fh:
		data = json.load(fh)

	teamProps = {}
	events = {}
	if "eventGroup" not in data:
		return
	for event in data["eventGroup"]["events"]:
		if "teamShortName1" not in event:
			game = convertDKTeam(event["teamName1"].lower()) + " @ " + convertDKTeam(event["teamName2"].lower())
		else:
			game = convertDKTeam(event["teamShortName1"].lower()) + " @ " + convertDKTeam(event["teamShortName2"].lower())
		if game not in teamProps:
			teamProps[game] = {}
		events[event["eventId"]] = game

	for catRow in data["eventGroup"]["offerCategories"]:
		if catRow["offerCategoryId"] != 523:
			continue
		for cRow in catRow["offerSubcategoryDescriptors"]:
			if cRow["subcategoryId"] != 4609:
				continue
			for offerRow in cRow["offerSubcategory"]["offers"]:
				for row in offerRow:
					game = events[row["eventId"]]
					team = convertDKTeam(row["label"].lower())
					odds1 = row["outcomes"][0]["oddsAmerican"]
					odds2 = row["outcomes"][1]["oddsAmerican"]
					if row["outcomes"][0]["label"].lower() == "under":
						odds1, odds2 = odds2, odds1

					teamProps[game][team] = {
						"line": row["outcomes"][0]["line"],
						"odds": ",".join([odds1, odds2])
					}

	with open(f"{prefix}static/nbaprops/teamProps.json", "w") as fh:
		json.dump(teamProps, fh, indent=4)

def writeGameLines(date):
	lines = {}
	if os.path.exists(f"{prefix}static/nbaprops/lines/{date}.json"):
		with open(f"{prefix}static/nbaprops/lines/{date}.json") as fh:
			lines = json.load(fh)

	time.sleep(0.3)
	url = "https://sportsbook-us-mi.draftkings.com//sites/US-MI-SB/api/v5/eventgroups/42648/categories/487/subcategories/4511?format=json"
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
		displayTeams[event["teamName1"].lower()] = event.get("teamShortName1", "").lower()
		displayTeams[event["teamName2"].lower()] = event.get("teamShortName2", "").lower()
		if "teamShortName1" not in event:
			game = convertDKTeam(event["teamName1"].lower()) + " @ " + convertDKTeam(event["teamName2"].lower())
		else:
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
					try:
						gameType = row["label"].lower().split(" ")[-1]
					except:
						continue

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

	with open(f"{prefix}static/nbaprops/lines/{date}.json", "w") as fh:
		json.dump(lines, fh, indent=4)

def writeH2H():
	ids = {
		"pts": [1215, 12512],
		"reb": [1216, 12513],
		"ast": [1217, 12514],
		"3ptm": [1218, 12515],
		"fgm": [1221, 12516],
		"to": [1220, 12517]
	}

	h2h = {}

	for prop in ids:
		time.sleep(0.3)
		url = f"https://sportsbook-us-mi.draftkings.com//sites/US-MI-SB/api/v5/eventgroups/42648/categories/{ids[prop][0]}/subcategories/{ids[prop][1]}?format=json"
		outfile = "out"
		call(["curl", "-k", url, "-o", outfile])

		with open("out") as fh:
			data = json.load(fh)

		events = {}
		if "eventGroup" not in data:
			continue
		for event in data["eventGroup"]["events"]:
			if "teamShortName1" not in event:
				game = convertDKTeam(event["teamName1"].lower()) + " @ " + convertDKTeam(event["teamName2"].lower())
			else:
				game = convertDKTeam(event["teamShortName1"].lower()) + " @ " + convertDKTeam(event["teamShortName2"].lower())
			if game not in h2h:
				h2h[game] = {}
			events[event["eventId"]] = game

		for catRow in data["eventGroup"]["offerCategories"]:
			if catRow["offerCategoryId"] != ids[prop][0]:
				continue
			for cRow in catRow["offerSubcategoryDescriptors"]:
				if cRow["subcategoryId"] == ids[prop][1]:
					for offerRow in cRow["offerSubcategory"]["offers"]:
						for row in offerRow:
							game = events[row["eventId"]]
							try:
								player1 = row["outcomes"][0]["label"].lower().replace(".", "").replace("'", "").replace("-", " ")
							except:
								continue
							odds1 = row["outcomes"][0]["oddsAmerican"]
							player2 = row["outcomes"][1]["label"].lower().replace(".", "").replace("'", "").replace("-", " ")
							odds2 = row["outcomes"][1]["oddsAmerican"]

							if prop not in h2h[game]:
								h2h[game][prop] = {}
							h2h[game][prop][f"{player1} v {player2}"] = ",".join([odds1, odds2])

	with open(f"{prefix}static/nbaprops/h2h.json", "w") as fh:
		json.dump(h2h, fh, indent=4)


@nbaprops_blueprint.route('/nbaprops')
def props_route():
	spread = line = 0
	prop = alt = date = teams = players = ""
	if request.args.get("prop"):
		prop = request.args.get("prop").replace(" ", "+")
	if request.args.get("alt"):
		alt = request.args.get("alt")
	if request.args.get("date"):
		date = request.args.get("date")
	if request.args.get("teams"):
		teams = request.args.get("teams")
	if request.args.get("players"):
		players = request.args.get("players")
	if request.args.get("line"):
		line = request.args.get("line")
	if request.args.get("spread"):
		spread = request.args.get("spread")
	return render_template("nbaprops.html", prop=prop, alt=alt, date=date, teams=teams, players=players, line=line, spread=spread)

@nbaprops_blueprint.route('/getH2HNBAProps')
def getH2HProps_route():
	res = []

	teamsArg = request.args.get("teams") or ""
	if teamsArg:
		teamsArg = teamsArg.lower().split(",")
	playersArg = request.args.get("players") or []
	if playersArg:
		playersArg = players.split(",")

	date = datetime.now()
	date = str(date)[:10]

	with open(f"{prefix}static/nbaprops/dates/{date}.json") as fh:
		propData = json.load(fh)
	with open(f"{prefix}static/basketballreference/totals.json") as fh:
		stats = json.load(fh)
	with open(f"{prefix}static/basketballreference/rankings.json") as fh:
		rankings = json.load(fh)
	with open(f"{prefix}static/basketballreference/schedule.json") as fh:
		schedule = json.load(fh)
	with open(f"{prefix}static/basketballreference/roster.json") as fh:
		roster = json.load(fh)
	with open(f"{prefix}static/nbaprops/h2h.json") as fh:
		h2h = json.load(fh)

	res = []
	playerStats = {}
	for game in h2h:
		teams = game.split(" @ ")
		for team in teams:
			if team not in playerStats:
				playerStats[team] = {}
			for file in glob.glob(f"{prefix}static/basketballreference/{team}/*.json"):
				dt = file.split("/")[-1][:-5]
				if dt not in playerStats[team]:
					with open(file) as fh:
						playerStats[team][dt] = json.load(fh)
		for prop in h2h[game]:
			for matchup in h2h[game][prop]:
				odds = h2h[game][prop][matchup].split(",")
				players = matchup.split(" v ")

				arrs = [[], []]
				lines = [0,0]
				playerTeams = ["", ""]
				for pIdx, player in enumerate(players):
					team = game.split(" @ ")[pIdx]
					if game in propData and player in propData[game]:
						try:
							lines[pIdx] = propData[game][player][prop]["line"]
						except:
							pass
					playerTeams[pIdx] = team
					for dt in sorted(playerStats[team], key=lambda k: datetime.strptime(k, "%Y-%m-%d"), reverse=True):
						if player in playerStats[team][dt] and playerStats[team][dt][player].get("min", 0) > 0:
							arrs[pIdx].append(playerStats[team][dt][player][prop])


				straightOver = straightTotal = 0
				for num1, num2 in zip(arrs[0], arrs[1]):
					if num1 == num2:
						continue
					elif num1 > num2:
						straightOver += 1
					straightTotal += 1
				if straightTotal:
					straightOver = round(straightOver * 100 / straightTotal)

				allPairsOver = allPairsTotal = allPairsOdds = 0
				for num1 in arrs[0]:
					for num2 in arrs[1]:
						if num1 == num2:
							continue
						elif num1 > num2:
							allPairsOver += 1
						allPairsTotal += 1
				if allPairsTotal:
					allPairsOver = round(allPairsOver * 100 / allPairsTotal)
					allPairsOdds = round((100*allPairsOver) / (-100+allPairsOver))
					if allPairsOver < 50:
						allPairsOdds = round((100*(100-allPairsOver)) / (-100+(100-allPairsOver)))

				team1, team2 = playerTeams[0], playerTeams[1]
				teamRank1 = teamRank2 = ""
				rankingsPos1 = roster[team1][players[0]]
				rankingsPos2 = roster[team2][players[1]]
				if rankingsPos1 == "F":
					rankingsPos1 = "PF"
				elif rankingsPos1 == "G":
					rankingsPos1 = "SG"
				if rankingsPos2 == "F":
					rankingsPos2 = "PF"
				elif rankingsPos2 == "G":
					rankingsPos2 = "SG"
				rankingsProp = prop
				if rankingsProp == "fgm":
					rankingsProp = "pts"

				if rankingsPos2 in rankings[team1] and rankingsProp in rankings[team1][rankingsPos2]:
					teamRank1 = rankings[team1][rankingsPos2][rankingsProp+"_rank"]
				if rankingsPos1 in rankings[team2] and rankingsProp in rankings[team2][rankingsPos1]:
					teamRank2 = rankings[team2][rankingsPos1][rankingsProp+"_rank"]

				res.append({
					"game": game,
					"prop": prop,
					"matchup": matchup,
					"player1": players[0].split(" ")[1].title(),
					"team1": team1,
					"rank1": teamRank1,
					"line1": lines[0],
					"odds1": odds[0],
					"log1": ",".join([str(x) for x in arrs[0]]),
					"player2": players[1].split(" ")[1].title(),
					"team2": team2,
					"rank2": teamRank2,
					"line2": lines[1],
					"odds2": odds[1],
					"log2": ",".join([str(x) for x in arrs[1]]),
					"straightOver": straightOver,
					"allPairsOver": allPairsOver,
					"allPairsOdds": allPairsOdds
				})

	return jsonify(res)

def writeAlts():
	url = "https://sportsbook.draftkings.com/event/sac-kings-%40-phi-76ers/28083724?subcategory=player-props&sgpmode=true"
	outfile = "out2"
	#call(["curl", "-k", url, "-o", outfile])
	soup = BS(open(outfile, 'rb').read(), "lxml")


@nbaprops_blueprint.route('/h2hnba')
def h2hprops_route():
	teams = players = ""
	if request.args.get("teams"):
		teams = request.args.get("teams")
	if request.args.get("players"):
		players = request.args.get("players")
	return render_template("h2hnba.html", teams=teams, players=players)

def getAvgSplits(schedule, scores):
	avgSplits = {}
	for dt in sorted(scores, key=lambda k: datetime.strptime(k, "%Y-%m-%d"), reverse=True):
		for team in scores[dt]:
			currTeams = [g.split(" @ ") for g in schedule[dt] if team in g.split(" @ ")][0]
			currOpp = currTeams[0] if team == currTeams[1] else currTeams[1]

			if team not in avgSplits:
				avgSplits[team] = {"lastAll": [], "oppLastAll": [], "winLoss": [[], []], "awayHome": [[], []]}
			if currOpp not in avgSplits:
				avgSplits[currOpp] = {"lastAll": [], "oppLastAll": [], "winLoss": [[], []], "awayHome": [[], []]}

			score = scores[dt][team]
			oppScore = scores[dt][currOpp]

			avgSplits[currTeams[0]]["awayHome"][0].append(scores[dt][currTeams[0]])
			avgSplits[currTeams[1]]["awayHome"][1].append(scores[dt][currTeams[1]])

			avgSplits[team]["lastAll"].append(score)
			avgSplits[team]["oppLastAll"].append(oppScore)
			avgSplits[currOpp]["lastAll"].append(oppScore)
			avgSplits[currOpp]["oppLastAll"].append(score)

			if score > oppScore:
				avgSplits[team]["winLoss"][0].append(score)
				avgSplits[currOpp]["winLoss"][1].append(oppScore)
			else:
				avgSplits[team]["winLoss"][1].append(score)
				avgSplits[currOpp]["winLoss"][0].append(oppScore)
	return avgSplits

@nbaprops_blueprint.route('/getNBATeamProps')
def getNBATeam_route():
	res = []

	teamsArg = request.args.get("teams") or ""
	if teamsArg:
		teamsArg = teamsArg.lower().split(",")

	date = datetime.now()
	date = str(date)[:10]
	if request.args.get("date"):
		date = request.args.get("date")

	with open(f"{prefix}static/basketballreference/scores.json") as fh:
		scores = json.load(fh)
	with open(f"{prefix}static/basketballreference/schedule.json") as fh:
		schedule = json.load(fh)
	with open(f"{prefix}static/nbaprops/teamProps.json") as fh:
		teamProps = json.load(fh)
	with open(f"{prefix}static/nbaprops/lines/{date}.json") as fh:
		gameLines = json.load(fh)

	avgSplits = getAvgSplits(schedule, scores)

	res = []
	for game in teamProps:
		gameSp = game.split(" @ ")
		for team in teamProps[game]:
			opp = gameSp[0] if team == gameSp[1] else gameSp[1]
			line = teamProps[game][team]["line"]
			odds = teamProps[game][team]["odds"].split(",")

			lastAll = avgSplits[team]["lastAll"]
			oppLastAll = avgSplits[opp]["oppLastAll"]
			winSplitAvg = lossSplitAvg = 0
			winLossSplits = avgSplits[team]["winLoss"]
			if len(winLossSplits[0]):
				winSplitAvg = round(sum(winLossSplits[0]) / len(winLossSplits[0]),2)
			if len(winLossSplits[1]):
				lossSplitAvg = round(sum(winLossSplits[1]) / len(winLossSplits[1]),2)
			winLoss = f"{winSplitAvg} - {lossSplitAvg}"

			awaySplitAvg = homeSplitAvg = 0
			awayHomeSplits = avgSplits[team]["awayHome"]
			if len(awayHomeSplits[0]):
				awaySplitAvg = round(sum(awayHomeSplits[0]) / len(awayHomeSplits[0]),2)
			if len(awayHomeSplits[1]):
				homeSplitAvg = round(sum(awayHomeSplits[1]) / len(awayHomeSplits[1]),2)
			awayHome = f"{awaySplitAvg} - {homeSplitAvg}"

			gameLine = ""
			if game in gameLines:
				gameOdds = gameLines[game]["moneyline"]["odds"].split(",")
				if team == game.split(" @ ")[0]:
					gameLine = gameOdds[0]
				else:
					gameLine = gameOdds[1]

			res.append({
				"team": team,
				"ppg": round(sum(lastAll) / len(lastAll), 1),
				"ppgL10": round(sum(lastAll[:10]) / len(lastAll[:10]), 1),
				"ppgL5": round(sum(lastAll[:5]) / len(lastAll[:5]), 1),
				"ppgL1": round(sum(lastAll[:1]) / len(lastAll[:1]), 1),
				"oppPPGA": round(sum(oppLastAll) / len(oppLastAll), 1),
				"oppPPGAL10": round(sum(oppLastAll[:10]) / len(oppLastAll[:10]), 1),
				"oppPPGAL5": round(sum(oppLastAll[:5]) / len(oppLastAll[:5]), 1),
				"oppPPGAL1": round(sum(oppLastAll[:1]) / len(oppLastAll[:1]), 1),
				"opp": opp,
				"line": line,
				"game": game,
				"over": odds[0],
				"under": odds[1],
				"ML": gameLine,
				"last10": ",".join([str(x) for x in lastAll[:10]]),
				"winLossSplits": winLoss,
				"awayHomeSplits": awayHome,
				"totalOver": round(len([x for x in lastAll if x > line]) * 100 / len(lastAll)),
				"oppTotalOver": round(len([x for x in oppLastAll if x > line]) * 100 / len(oppLastAll)),
			})

	return jsonify(res)

@nbaprops_blueprint.route('/teamsnba')
def teamsnba_route():
	teams = players = ""
	if request.args.get("teams"):
		teams = request.args.get("teams")
	return render_template("teamsnba.html", teams=teams)

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("-c", "--cron", action="store_true", help="Start Cron Job")
	parser.add_argument("-d", "--date", help="Date")
	parser.add_argument("--alts", help="Alts", action="store_true")
	parser.add_argument("--zero", help="Zero CustomProp Odds", action="store_true")
	parser.add_argument("--lineups", help="Lineups", action="store_true")
	parser.add_argument("--lines", action="store_true", help="Game Lines")
	parser.add_argument("--teamProps", help="Team Props", action="store_true")
	parser.add_argument("--skip-lineups", help="Skip Lineups", action="store_true")
	parser.add_argument("--h2h", help="H2H", action="store_true")
	parser.add_argument("-w", "--week", help="Week", type=int)

	args = parser.parse_args()

	date = args.date
	if not date:
		date = datetime.now()
		date = str(date)[:10]

	if args.cron:
		if not args.skip_lineups:
			writeLineups()
		writeProps(date)
		writeTeamProps()
		writeH2H()
		writeGameLines(date)
	elif args.alts:
		writeAlts()
	elif args.h2h:
		writeH2H()
	elif args.lines:
		writeGameLines(date)
	elif args.teamProps:
		writeTeamProps()
	elif args.lineups:
		writeLineups()
	elif args.zero:
		zeroProps()