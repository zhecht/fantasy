#from selenium import webdriver
from flask import *
from subprocess import call
from bs4 import BeautifulSoup as BS
from sys import platform
from datetime import datetime

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
	actionNetworkBookIds = {
		68: "draftkings",
		69: "fanduel"
	}
	propMap = {
		"3ptm": "core_bet_type_21_3fgm",
		"reb": "core_bet_type_23_rebounds",
		"stl": "core_bet_type_24_steals",
		"blk": "core_bet_type_25_blocks",
		"ast": "core_bet_type_26_assists",
		"pts": "core_bet_type_27_points",
		"pts+reb+ast": "core_bet_type_85_points_rebounds_assists",
		"pts+reb": "core_bet_type_86_points_rebounds",
		"pts+ast": "core_bet_type_87_points_assists",
		"reb+ast": "core_bet_type_88_rebounds_assists",
		"stl+blk": "core_bet_type_89_steals_blocks"
	}
	props = {}
	optionTypes = {}
	for prop in ["pts", "ast", "reb", "blk", "stl", "pts+ast", "pts+reb", "pts+reb+ast", "reb+ast", "stl+blk", "3ptm"]:

		path = f"{prefix}static/nbaprops/{prop}.json"
		url = f"https://api.actionnetwork.com/web/v1/leagues/4/props/{propMap[prop]}?bookIds=69,68&date={date.replace('-', '')}"
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

	teams = request.args.get("teams") or ""
	if teams:
		teams = teams.lower().split(",")
	alt = request.args.get("alt") or ""
	players = request.args.get("players") or []
	if players:
		playes = players.split(",")

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

	oppOvers = getOppOvers(schedule, roster)
	#propData = customPropData(propData)

	props = []
	for team in propData:
		espnTeam = fixNBATeam(team)
		opp = game = ""
		if date in schedule:
			for t in schedule[date]:
				game = t
				t = t.split(" @ ")
				if espnTeam in t:
					if t.index(espnTeam) == 0:
						opp = t[1]
					else:
						opp = t[0]
					break

		if teams and team not in teams:
			continue

		for propName in propData[team]:
			name = propName.replace("-", " ").replace(".", "").replace("'", "")

			if players and name not in players:
				continue

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

				totalOverPerMin = totalOver = totalOverLast5 = totalGames = avgVariance = 0
				last5 = []
				lastAll = []
				lastAllPerMin = []
				hit = False
				if line and avgMin:
					files = sorted(glob.glob(f"{prefix}static/basketballreference/{espnTeam}/*.json"), key=lambda k: datetime.strptime(k.split("/")[-1].replace(".json", ""), "%Y-%m-%d"), reverse=True)
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

				pos = roster[espnTeam][name]

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

				props.append({
					"game": game,
					"player": name.title(),
					"team": espnTeam.upper(),
					"opponent": opp,
					"hit": hit,
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

	if not alt:
		teamTotals(date, schedule)
		write_csvs(props)
		h2h(props)
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

				allPairsOver = allPairsTotal = 0
				for num1 in arrs[0]["lastAll"].split(","):
					for num2 in arrs[1]["lastAll"].split(","):
						if int(num1) == int(num2):
							continue
						elif int(num1) > int(num2):
							allPairsOver += 1
						allPairsTotal += 1
				if allPairsTotal:
					allPairsOver = round(allPairsOver * 100 / allPairsTotal)

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
	headers = "\t".join(["NAME","POS","MIN","TEAM","OPP","OPP RANK","PROP","LINE","SZN AVG","% OVER","L5 % OVER","LAST 7 GAMES ➡️","LAST YR % OVER","OVER", "UNDER"])
	reddit = "|".join(headers.split("\t"))
	reddit += "\n:--|:--|:--|:--|:--|:--|:--|:--|:--|:--|:--|:--|:--|:--|:--"

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
			if underOdds == '-inf':
				underOdds = 0
			if int(overOdds) > 0:
				overOdds = "'"+overOdds
			if int(underOdds) > 0:
				underOdds = "'"+underOdds
			try:
				csvs[prop] += "\n" + "\t".join([row["player"], row["position"], str(row["avgMin"]), row["team"], row["opponent"].upper(), addNumSuffix(row["oppRank"]), row["propType"], str(row["line"]), str(row["avg"]), f"{row['totalOver']}%", f"{row['totalOverLast5']}%", row["last5"], f"{row['lastTotalOver']}%",overOdds, underOdds])
			except:
				pass

	# add full rows
	csvs["full_name"] = headers
	rows = sorted(splitProps["full"], key=lambda k: (k["player"], -k["totalOverLast5"], -k["totalOver"]))
	for row in rows:
		overOdds = row["overOdds"]
		underOdds = row["underOdds"]
		if underOdds == '-inf':
			underOdds = 0
		if int(overOdds) > 0:
			overOdds = "'"+overOdds
		if int(underOdds) > 0:
			underOdds = "'"+underOdds
		try:
			csvs["full_name"] += "\n" + "\t".join([row["player"], row["position"], str(row["avgMin"]), row["team"], row["opponent"].upper(), addNumSuffix(row["oppRank"]), row["propType"], str(row["line"]), str(row["avg"]), f"{row['totalOver']}%", f"{row['totalOverLast5']}%", row["last5"], f"{row['lastTotalOver']}%",overOdds, underOdds])
		except:
			pass

	csvs["full_hit"] = headers
	rows = sorted(splitProps["full"], key=lambda k: (k["totalOverLast5"], k["totalOver"]), reverse=True)
	for row in rows:
		overOdds = row["overOdds"]
		underOdds = row["underOdds"]
		if underOdds == '-inf':
			underOdds = 0
		if int(overOdds) > 0:
			overOdds = "'"+overOdds
		if int(underOdds) > 0:
			underOdds = "'"+underOdds
		try:
			csvs["full_hit"] += "\n" + "\t".join([row["player"], row["position"], str(row["avgMin"]), row["team"], row["opponent"].upper(), addNumSuffix(row["oppRank"]), row["propType"], str(row["line"]), str(row["avg"]), f"{row['totalOver']}%", f"{row['totalOverLast5']}%", row["last5"], f"{row['lastTotalOver']}%",overOdds, underOdds])
		except:
			pass

	# add top 4 to reddit
	for prop in ["pts", "reb", "ast"]:
		rows = sorted(splitProps[prop], key=lambda k: (k["totalOverLast5"], k["totalOver"]), reverse=True)
		for row in rows[:4]:
			overOdds = row["overOdds"]
			underOdds = row["underOdds"]
			try:
				reddit += "\n" + "|".join([row["player"], row["position"], str(row["avgMin"]), row["team"], row["opponent"].upper(), addNumSuffix(row["oppRank"]), row["propType"], str(row["line"]), str(row["avg"]), f"{row['totalOver']}%", f"{row['totalOverLast5']}%", row["last5"], f"{row['lastTotalOver']}%",overOdds, underOdds])
			except:
				pass
		reddit += "\n-|-|-|-|-|-|-|-|-|-|-|-|-|-|-"

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
	elif prop == "pts":
		return "fgpg"
	return prop[0]+"pg"

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
	if team == "was":
		return "wsh"
	elif team == "pho":
		return "phx"
	return team

def writeH2H():
	ids = {
		"pts": 12186,
		"reb": 12185,
		"ast": 12184,
		"3ptm": 12315
	}

	h2h = {}
	for prop in ids:
		time.sleep(0.5)
		url = f"https://sportsbook-us-mi.draftkings.com//sites/US-MI-SB/api/v5/eventgroups/42648/categories/1206/subcategories/{ids[prop]}?format=json"
		outfile = "out"
		call(["curl", "-k", url, "-o", outfile])

		with open("out") as fh:
			data = json.load(fh)

		events = {}
		if "eventGroup" not in data:
			continue
		for event in data["eventGroup"]["events"]:
			game = convertDKTeam(event["teamShortName1"].lower()) + " @ " + convertDKTeam(event["teamShortName2"].lower())
			if game not in h2h:
				h2h[game] = {}
			events[event["eventId"]] = game

		for catRow in data["eventGroup"]["offerCategories"]:
			if not catRow["name"].lower().startswith("h2h"):
				continue
			for cRow in catRow["offerSubcategoryDescriptors"]:
				if cRow["subcategoryId"] == ids[prop]:
					for offerRow in cRow["offerSubcategory"]["offers"]:
						for row in offerRow:
							game = events[row["eventId"]]
							player1 = row["outcomes"][0]["label"].lower().replace(".", "").replace("'", "")
							odds1 = row["outcomes"][0]["oddsAmerican"]
							player2 = row["outcomes"][1]["label"].lower().replace(".", "").replace("'", "")
							odds2 = row["outcomes"][1]["oddsAmerican"]

							if prop not in h2h[game]:
								h2h[game][prop] = {}
							h2h[game][prop][f"{player1} v {player2}"] = ",".join([odds1, odds2])

	with open(f"{prefix}static/nbaprops/h2h.json", "w") as fh:
		json.dump(h2h, fh, indent=4)

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("-c", "--cron", action="store_true", help="Start Cron Job")
	parser.add_argument("-d", "--date", help="Date")
	parser.add_argument("--zero", help="Zero CustomProp Odds", action="store_true")
	parser.add_argument("--lineups", help="Lineups", action="store_true")
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
		writeH2H()
	elif args.h2h:
		writeH2H()
	elif args.lineups:
		writeLineups()
	elif args.zero:
		zeroProps()