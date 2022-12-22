#from selenium import webdriver
from flask import *
from subprocess import call
from bs4 import BeautifulSoup as BS
from sys import platform
from datetime import datetime
from datetime import timedelta

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

def getSplits(rankings, schedule, ttoi, dateArg):
	splits = {}
	for team in rankings:
		splits[team] = {}

		for key, which in zip(["savesPer60", "oppSavesAgainstPer60"], ["SV/GP", "OPP SV/GP"]):
			for period in ["", "last1", "last3", "last5"]:
				if key.startswith("opp"):
					if not period:
						splits[team][key+period.capitalize()] = round((rankings[team]["tot"][which]*ttoi[team]["oppTTOI"])/(60*rankings[team]["tot"]["GP"]), 1)
					else:
						splits[team][key+period.capitalize()] = round((rankings[team][period][which]*ttoi[team]["oppTTOI"+period[0].upper()+period[-1]])/(60*rankings[team][period]["GP"]), 1)
				else:
					if not period:
						splits[team][key+period.capitalize()] = round((rankings[team]["tot"][which]*ttoi[team]["ttoi"])/(60*rankings[team]["tot"]["GP"]), 1)
					else:
						splits[team][key+period.capitalize()] = round((rankings[team][period][which]*ttoi[team]["ttoi"+period[0].upper()+period[-1]])/(60*rankings[team][period]["GP"]), 1)

	today = datetime.now()
	today = str(today)[:10]

	for team in splits:
		opps = {}
		for date in sorted(schedule, key=lambda k: datetime.strptime(k, "%Y-%m-%d"), reverse=True):
			if date == dateArg or datetime.strptime(date, "%Y-%m-%d") > datetime.strptime(dateArg, "%Y-%m-%d"):
				continue
			for game in schedule[date]:
				gameSp = game.split(" @ ")
				if team in gameSp:
					opp = gameSp[0] if team == gameSp[1] else gameSp[1]
					opps[date] = opp

		savesAboveAvg = []
		oppSavesAgainstAboveAvg = []
		for date in sorted(opps, key=lambda k: datetime.strptime(k, "%Y-%m-%d"), reverse=True):
			
			opp = opps[date]

			try:
				with open(f"{prefix}static/hockeyreference/{team}/{date}.json") as fh:
					stats = json.load(fh)
				with open(f"{prefix}static/hockeyreference/{opp}/{date}.json") as fh:
					oppStats = json.load(fh)
			except:
				continue
			
			saves = 0
			for player in stats:
				saves += stats[player].get("sv", 0)
			oppSavesAgainst = 0
			for player in oppStats:
				oppSavesAgainst += oppStats[player].get("sv", 0)
			
			if saves == 0:
				print(team,date,saves)
			if oppSavesAgainst == 0:
				print(opp,date,oppSavesAgainst)

			oppSvAgainstPer60 = splits[opp]["oppSavesAgainstPer60"]
			savesAboveAvg.append((saves / oppSvAgainstPer60) - 1)

			savesPer60 = splits[team]["savesPer60"]
			oppSavesAgainstAboveAvg.append((oppSavesAgainst / savesPer60) - 1)


		splits[team]["savesAboveAvg"] = round(sum(savesAboveAvg) / len(savesAboveAvg), 3)
		splits[team]["savesAboveAvgLast5"] = round(sum(savesAboveAvg[:5]) / len(savesAboveAvg[:5]), 3)
		splits[team]["savesAboveAvgLast3"] = round(sum(savesAboveAvg[:3]) / len(savesAboveAvg[:3]), 3)
		splits[team]["oppSavesAgainstAboveAvg"] = round(sum(oppSavesAgainstAboveAvg) / len(oppSavesAgainstAboveAvg), 3)
		splits[team]["oppSavesAgainstAboveAvgLast5"] = round(sum(oppSavesAgainstAboveAvg[:5]) / len(oppSavesAgainstAboveAvg[:5]), 3)
		splits[team]["oppSavesAgainstAboveAvgLast3"] = round(sum(oppSavesAgainstAboveAvg[:3]) / len(oppSavesAgainstAboveAvg[:3]), 3)
	return splits

def getOpportunitySplits(opportunities):
	oppSplits = {}

	for team in opportunities:
		oppSplits[team] = {}
		for period in opportunities[team]:
			oppSplits[team][period] = opportunities[team][period]
			for stat in ["cf", "ca", "ff", "fa", "sf", "sa", "scf", "sca"]:
				oppSplits[team][period][stat+"Per60"] = round(opportunities[team][period][stat]/opportunities[team][period]["toi"]*60, 1)

		formats = {
			"cf": "corsi",
			"ff": "fenwick",
			"sf": "shots",
			"scf": "scoring",
			"ca": "corsiAgainst",
			"fa": "fenwickAgainst",
			"sa": "shotsAgainst",
			"sca": "scoringAgainst"
		}

		for stat in formats:
			display = []
			for period in ["tot", "last10", "last5", "last3"]:
				pct = oppSplits[team][period][stat.replace('a','f')+'%']
				if "Against" in formats[stat]:
					pct = 100-pct
				display.append(f"{round(pct, 1)}% ({oppSplits[team][period][stat+'Per60']})")
			oppSplits[team][formats[stat]] = " // ".join(display)
	return oppSplits

@nhlprops_blueprint.route('/getNHLProps')
def getProps_route():
	res = []

	teams = request.args.get("teams") or ""
	if teams:
		teams = teams.lower().split(",")
	playersArg = request.args.get("players") or ""
	if playersArg:
		playersArg = playersArg.lower().split(",")
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
	with open(f"{prefix}static/hockeyreference/ttoi.json") as fh:
		ttoi = json.load(fh)
	with open(f"{prefix}static/hockeyreference/opportunities.json") as fh:
		opportunities = json.load(fh)

	opportunitySplits = getOpportunitySplits(opportunities)

	gameLines = {}
	if os.path.exists(f"{prefix}static/nhlprops/lines/{date}.json"):
		with open(f"{prefix}static/nhlprops/lines/{date}.json") as fh:
			gameLines = json.load(fh)
	with open(f"{prefix}static/nhlprops/goalies.json") as fh:
		goalies = json.load(fh)
	with open(f"{prefix}static/nhlprops/expected.json") as fh:
		expected = json.load(fh)

	goalieLines(propData)
	splits = getSplits(rankings, schedule, ttoi, date)

	allGoalies = {}
	for game in propData:
		teamSp = game.split(" @ ")
		for player in propData[game]:
			if "sv" not in propData[game][player]:
				continue
			shortFirstName = player.split(" ")[0][0]
			restName = " ".join(player.title().split(" ")[1:])
			name = f"{shortFirstName.upper()}. {restName.replace('-', ' ')}"
			if name in stats[teamSp[0]]:
				team = teamSp[0]
			else:
				team = teamSp[1]
			allGoalies[team] = player

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

			if playersArg and player not in playersArg:
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
				awayHomeSplits = [[],[]]
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
								val = 0.0
								if convertedProp == "pts":
									val = gameStats[name]["a"] + gameStats[name]["g"]
								elif convertedProp in gameStats[name]:
									val = gameStats[name][convertedProp]

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
									if val > float(line):
										hit = True

								if float(val) > float(line):
									if chkDate != date:
										totalOver += 1
										if len(last5) < 5:
											totalOverLast5 += 1

								if len(last5) < 10:
									v = str(int(val))
									if chkDate == date:
										v = f"'{v}'"
										last5.append(v)
										continue
									last5.append(v)

								if chkDate == date or datetime.strptime(chkDate, "%Y-%m-%d") > datetime.strptime(date, "%Y-%m-%d"):
									continue

								totalGames += 1
								valPerMin = float(val / minutes)
								teamScore = scores[chkDate][team]
								oppScore = scores[chkDate][pastOpp]
								winLossVal = valPerMin
								if prop == "sv":
									winLossVal *= 60
								else:
									winLossVal *= avgMin

								if teamIsAway:
									awayHomeSplits[0].append(val)
								else:
									awayHomeSplits[1].append(val)

								if teamScore > oppScore:
									winLossSplits[0].append(winLossVal)
								elif teamScore < oppScore:
									winLossSplits[1].append(winLossVal)

								linePerMin = float(line) / avgMin
								#if valPerMin > linePerMin:
								#	totalOver += 1 
				if totalGames:
					totalOver = round((totalOver / totalGames) * 100)
					
					realLast5 = [x for x in last5 if "'" not in x]
					last5Size = len(realLast5) if len(realLast5) < 5 else 5
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

				awaySplitAvg = homeSplitAvg = 0
				if len(awayHomeSplits[0]):
					awaySplitAvg = round(sum(awayHomeSplits[0]) / len(awayHomeSplits[0]),2)
				if len(awayHomeSplits[1]):
					homeSplitAvg = round(sum(awayHomeSplits[1]) / len(awayHomeSplits[1]),2)
				awayHome = f"{awaySplitAvg} - {homeSplitAvg}"

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

				gameLine = 0
				if game in gameLines:
					gameOdds = gameLines[game]["moneyline"]["odds"].split(",")
					if team == game.split(" @ ")[0]:
						gameLine = gameOdds[0]
					else:
						gameLine = gameOdds[1]

				savesAboveExp = gsaa = "-"
				if prop == "sv":
					p = player.replace("-", " ")
					if p not in expected:
						continue
					savesAboveExp = round((float(expected[p]["xgoals"])-float(expected[p]["goals"]))*60*60 / float(expected[p]["icetime"]), 3)
					try:
						gsaa = float(goalies[team][p]["gsaa"])
					except:
						gsaa = "-"
				else:
					if opp in allGoalies:
						goalie = allGoalies[opp]
						if goalie in expected:
							savesAboveExp = round((float(expected[goalie]["xgoals"])-float(expected[goalie]["goals"]))*60*60 / float(expected[goalie]["icetime"]), 3)
						else:
							savesAboveExp = "-"
						try:
							gsaa = float(goalies[opp][goalie]["gsaa"])
						except:
							gsaa = "-"

				props.append({
					"player": player.title(),
					"team": team.upper(),
					"opponent": opp.upper(),
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
					"awayHome": "A" if team == game.split(" @ ")[0] else "H",
					"awayHomeSplits": awayHome,
					"savesAboveExp": savesAboveExp,
					"gsaa": gsaa,
					"corsi": opportunitySplits[team]["corsi"],
					"fenwick": opportunitySplits[team]["fenwick"],
					"shots": opportunitySplits[team]["shots"],
					"scoring": opportunitySplits[team]["scoring"],
					"corsiAgainst": opportunitySplits[team]["corsiAgainst"],
					"fenwickAgainst": opportunitySplits[team]["fenwickAgainst"],
					"shotsAgainst": opportunitySplits[team]["shotsAgainst"],
					"scoringAgainst": opportunitySplits[team]["scoringAgainst"],
					"oppCorsi": opportunitySplits[opp]["corsi"],
					"oppFenwick": opportunitySplits[opp]["fenwick"],
					"oppShots": opportunitySplits[opp]["shots"],
					"oppScoring": opportunitySplits[opp]["scoring"],
					"oppCorsiAgainst": opportunitySplits[opp]["corsiAgainst"],
					"oppFenwickAgainst": opportunitySplits[opp]["fenwickAgainst"],
					"oppShotsAgainst": opportunitySplits[opp]["shotsAgainst"],
					"oppScoringAgainst": opportunitySplits[opp]["scoringAgainst"],

					"savesPerGame": round(rankings[team]["tot"]["SV/GP"], 1),
					"savesPerGameLast1": round(rankings[team]["last1"]["SV/GP"], 1),
					"savesPerGameLast3": round(rankings[team]["last3"]["SV/GP"], 1),
					"savesPerGameLast5": round(rankings[team]["last5"]["SV/GP"], 1),
					"savesPer60": splits[team]["savesPer60"],
					"savesPer60Last1": splits[team]["savesPer60Last1"],
					"savesPer60Last3": splits[team]["savesPer60Last3"],
					"savesPer60Last5": splits[team]["savesPer60Last5"],
					"shotsPerGame": round(rankings[team]["tot"]["S/GP"], 1),
					"shotsPerGameLast5": round(rankings[team]["last5"]["S/GP"], 1),
					"shotsAgainstPerGame": round(rankings[team]["tot"]["SA/GP"], 1),
					"shotsAgainstPerGameLast5": round(rankings[team]["last5"]["SA/GP"], 1),
					#"oppPtsPerGame": round((rankings[opp]["tot"]["GA"] / rankings[opp]["tot"]["GP"]) + (rankings[opp]["tot"]["OPP A"] / rankings[opp]["tot"]["GP"]), 1),
					#"oppPtsPerGameLast5": round((rankings[opp]["last5"]["GA"] / rankings[opp]["last5"]["GP"]) + (rankings[opp]["last5"]["OPP A"] / rankings[opp]["last5"]["GP"]), 1),
					"oppSavesAgainstPer60": splits[opp]["oppSavesAgainstPer60"],
					"oppSavesAgainstPer60Last1": splits[opp]["oppSavesAgainstPer60Last1"],
					"oppSavesAgainstPer60Last3": splits[opp]["oppSavesAgainstPer60Last3"],
					"oppSavesAgainstPer60Last5": splits[opp]["oppSavesAgainstPer60Last5"],
					"oppShotsAgainstPerGame": round(rankings[opp]["tot"]["SA/GP"], 1),
					"oppShotsAgainstPerGameLast5": round(rankings[opp]["last5"]["SA/GP"], 1),
					"savesProj": round(splits[team]["savesPer60"]+splits[team]["savesPer60"]*splits[opp]["oppSavesAgainstAboveAvg"], 1),
					"savesProjLast5": round(splits[team]["savesPer60Last5"]+splits[team]["savesPer60Last5"]*splits[opp]["oppSavesAgainstAboveAvgLast5"], 1),
					"savesProjLast3": round(splits[team]["savesPer60Last3"]+splits[team]["savesPer60Last3"]*splits[opp]["oppSavesAgainstAboveAvgLast3"], 1),
					"oppSavesAgainstProj": round(splits[opp]["oppSavesAgainstPer60"]+splits[opp]["oppSavesAgainstPer60"]*splits[team]["savesAboveAvg"], 1),
					"oppSavesAgainstProjLast5": round(splits[opp]["oppSavesAgainstPer60Last5"]+splits[opp]["oppSavesAgainstPer60Last5"]*splits[team]["savesAboveAvgLast5"], 1),
					"oppSavesAgainstProjLast3": round(splits[opp]["oppSavesAgainstPer60Last3"]+splits[opp]["oppSavesAgainstPer60Last3"]*splits[team]["savesAboveAvgLast3"], 1),
					"totalOver": totalOver,
					"totalOverLast5": totalOverLast5,
					"lastTotalOver": lastTotalOver,
					"last5": ",".join(last5),
					"overOdds": overOdds,
					"underOdds": underOdds,
					"overUnder": f"{overOdds} / {underOdds}"
				})

	teamTotals()
	writeCsvs(props)
	return jsonify(props)

@nhlprops_blueprint.route('/nhlprops')
def props_route():
	prop = alt = date = teams = players = ""
	if request.args.get("prop"):
		prop = request.args.get("prop")
	if request.args.get("alt"):
		alt = request.args.get("alt")
	if request.args.get("date"):
		date = request.args.get("date")
	if request.args.get("teams"):
		teams = request.args.get("teams")
	if request.args.get("players"):
		players = request.args.get("players")

	bets = ",".join(["erik karlsson", "drake batherson", "jake guentzel", "artemi panarin", "noah cates", "ivan provorov", "quinn hughes", "tristan jarry", "filip gustavsson", "carter hart"])
	return render_template("nhlprops.html", prop=prop, alt=alt, date=date, teams=teams, bets=bets, players=players)

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


def writeCsvs(props):
	csvs = {}
	splitProps = {"full": []}
	headers = "\t".join(["NAME","TEAM","ML","A/H","PROP","LINE","SZN AVG","W-L Splits","A-H Splits","% OVER","L5 % OVER","LAST 10 GAMES","LAST YR % OVER","OVER","UNDER"])
	reddit = "|".join(headers.split("\t"))
	reddit += "\n:--|:--|:--|:--|:--|:--|:--|:--|:--|:--|:--|:--|:--|:--|:--"

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
			gameLine = row["gameLine"]
			if int(overOdds) > 0:
				overOdds = "'"+overOdds
			if int(underOdds) > 0:
				underOdds = "'"+underOdds
			if int(gameLine) > 0:
				gameLine = "'"+gameLine
			avg = row["avg"]
			#if avg >= row["line"]:
			#	avg = f"**{avg}**"
			csvs[prop] += "\n" + "\t".join([str(x) for x in [row["player"], row["team"], gameLine, row["awayHome"], row["propType"], row["line"], avg, row["winLossSplits"], row["awayHomeSplits"], f"{row['totalOver']}%", f"{row['totalOverLast5']}%", row["last5"], f"{row['lastTotalOver']}%",overOdds, underOdds]])

	# add full rows
	csvs["full"] = headers
	rows = sorted(splitProps["full"], key=lambda k: (k["player"]))
	for row in rows:
		overOdds = row["overOdds"]
		underOdds = row["underOdds"]
		gameLine = row["gameLine"]
		if int(overOdds) > 0:
			overOdds = "'"+overOdds
		if int(underOdds) > 0:
			underOdds = "'"+underOdds
		if int(gameLine) > 0:
			gameLine = "'"+gameLine
		avg = row["avg"]
		#if avg >= row["line"]:
		#	avg = f"**{avg}**"
		csvs["full"] += "\n" + "\t".join([str(x) for x in [row["player"], row["team"], gameLine, row["awayHome"], row["propType"], row["line"], avg, row["winLossSplits"], row["awayHomeSplits"], f"{row['totalOver']}%", row["last5"], f"{row['lastTotalOver']}%",overOdds, underOdds]])

	# add top 4 to reddit
	for prop in ["sog", "pts"]:
		if prop in splitProps:
			rows = sorted(splitProps[prop], key=lambda k: (k["totalOverLast5"], k["totalOver"]), reverse=True)
			for row in rows[:4]:
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
				reddit += "\n" + "|".join([str(x) for x in [row["player"], row["team"], row["gameLine"], row["awayHome"], row["propType"], row["line"], avg, winLossSplits, awayHomeSplits, f"{row['totalOver']}%", f"{row['totalOverLast5']}%", row["last5"], f"{row['lastTotalOver']}%",overOdds, underOdds]])
		reddit += "\n-|-|-|-|-|-|-|-|-|-|-|-|-|-|-"

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

def convertDKTeam(team):
	if team == "was":
		return "wsh"
	return team

def writeGameLines(date):
	lines = {}
	if os.path.exists(f"{prefix}static/nhlprops/lines/{date}.json"):
		with open(f"{prefix}static/nhlprops/lines/{date}.json") as fh:
			lines = json.load(fh)

	time.sleep(0.3)
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

	with open(f"{prefix}static/nhlprops/lines/{date}.json", "w") as fh:
		json.dump(lines, fh, indent=4)


def writeGoalieProps(date):

	time.sleep(0.3)
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
	if os.path.exists(f"{prefix}static/nhlprops/dates/{date}.json"):
		with open(f"{prefix}static/nhlprops/dates/{date}.json") as fh:
			props = json.load(fh)

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

def writeGoalieStats():
	url = "https://www.hockey-reference.com/leagues/NHL_2023_goalies.html"
	outfile = "out"
	call(["curl", "-k", url, "-o", outfile])
	soup = BS(open(outfile, 'rb').read(), "lxml")

	rows = soup.findAll("tr")
	headers = []
	for header in rows[1].findAll("th")[1:]:
		headers.append(header.text.lower())

	stats = {}
	for tr in rows[2:]:
		if "thead" in tr.get("class", []):
			continue
		rowStats = {}
		for hdr, td in zip(headers, tr.findAll("td")):
			val = td.text
			if "." in val:
				val = float(val)
			else:
				try:
					val = int(val)
				except:
					pass
			rowStats[hdr] = val

		player = rowStats["player"].lower().replace("-", " ")
		team = rowStats["tm"].lower()
		if team == "lak":
			team = "la"
		elif team == "sjs":
			team = "sj"
		elif team == "njd":
			team = "nj"
		elif team == "veg":
			team = "vgk"

		if team not in stats:
			stats[team] = {}

		stats[team][player] = rowStats

	with open(f"{prefix}static/nhlprops/goalies.json", "w") as fh:
		json.dump(stats, fh, indent=4)

def writeExpectations():
	url = "https://www.moneypuck.com/moneypuck/playerData/seasonSummary/2022/regular/goalies.csv"
	outfile = f"{prefix}static/nhlprops/goalies.csv"

	goalies = {}
	lines = open(outfile).readlines()
	headers = []
	for header in lines[0].split(","):
		headers.append(header.lower())

	for line in lines[1:]:
		data = {}
		for header, val in zip(headers,line.replace("\n", "").split(",")):
			data[header] = val
		if data["situation"] != "all":
			continue
		goalies[data["name"].lower().replace("-", " ")] = data

	with open(f"{prefix}static/nhlprops/expected.json", "w") as fh:
		json.dump(goalies, fh, indent=4)

def convertNaturalStatTeam(team):
	if team.startswith("columbus"):
		return "cbj"
	elif team.endswith("rangers"):
		return "nyr"
	elif team.endswith("islanders"):
		return "nyi"
	elif team.endswith("sharks"):
		return "sj"
	elif team.endswith("capitals"):
		return "wsh"
	elif team.endswith("predators"):
		return "nsh"
	elif team.endswith("knights"):
		return "vgk"
	elif team.endswith("lightning"):
		return "tb"
	elif team.endswith("kings"):
		return "la"
	elif team.endswith("canadiens"):
		return "mtl"
	elif team.endswith("panthers"):
		return "fla"
	elif team.endswith("jets"):
		return "wpg"
	elif team.endswith("devils"):
		return "nj"
	elif team.endswith("flames"):
		return "cgy"

	return team.replace(" ", "")[:3]

def writeOpportunities():

	date = datetime.now()
	date = str(date)[:10]

	twoWeeksAgo = datetime.now() - timedelta(days=10)
	twoWeeksAgo = str(twoWeeksAgo)[:10]
	oneWeekAgo = datetime.now() - timedelta(days=6)
	oneWeekAgo = str(oneWeekAgo)[:10]

	baseUrl = "https://www.naturalstattrick.com/teamtable.php?fromseason=20222023&thruseason=20222023&stype=2&sit=all&score=all&rate=n&team=all&loc=B"
	periods = {
		"last10": "&gpf=10",
		"last5": f"&fd={twoWeeksAgo}&td={date}",
		"last3": f"&fd={oneWeekAgo}&td={date}",
		"tot": ""
	}

	opps = {}

	for period in periods:
		url = f"{baseUrl}{periods[period]}"
		outfile = "out"
		time.sleep(0.3)
		call(["curl", "-k", url, "-o", outfile])
		soup = BS(open(outfile, 'rb').read(), "lxml")

		headers = []
		for th in soup.find("tr").findAll("th")[1:]:
			headers.append(th.text.strip().lower().replace(" ", ""))

		for row in soup.findAll("tr")[1:]:
			rowStats = {}
			for hdr, td in zip(headers, row.findAll("td")[1:]):
				val = td.text
				try:
					if "." in val:
						val = float(val)
					else:
						val = int(val)
				except:
					pass
				rowStats[hdr] = val

			team = convertNaturalStatTeam(rowStats["team"].lower())
			rowStats["toi"] = int(rowStats["toi"].split(":")[0]) + (int(rowStats["toi"].split(":")[-1]) / 60)

			if team not in opps:
				opps[team] = {}
			opps[team][period] = rowStats

	with open(f"{prefix}static/hockeyreference/opportunities.json", "w") as fh:
		json.dump(opps, fh, indent=4)


if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("-c", "--cron", action="store_true", help="Start Cron Job")
	parser.add_argument("--lines", action="store_true", help="Game Lines")
	parser.add_argument("--goalies", action="store_true", help="Goalie Stats")
	parser.add_argument("--opp", action="store_true", help="Opportunities")
	parser.add_argument("-d", "--date", help="Date")
	parser.add_argument("-w", "--week", help="Week", type=int)

	args = parser.parse_args()

	date = args.date
	if not date:
		date = datetime.now()
		date = str(date)[:10]

	if args.lines:
		writeGameLines(date)
		writeExpectations()
	elif args.goalies:
		writeExpectations()
		writeGoalieStats()
	elif args.opp:
		writeOpportunities()
	elif args.cron:
		writeProps(date)
		writeGoalieProps(date)
		writeGoalieStats()
		writeExpectations()
		writeGameLines(date)
		writeOpportunities()