#from selenium import webdriver
from flask import *
from subprocess import call
from bs4 import BeautifulSoup as BS
from sys import platform

import glob
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

from datetime import datetime

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
	if team == "arz":
		return "ari"
	elif team == "blt":
		return "bal"
	elif team == "clv":
		return "cle"
	elif team == "hst":
		return "hou"
	elif team == "la":
		return "lar"
	elif team == "sdg":
		return "lac"
	elif team == "was":
		return "wsh"
	return team

def getOppTotPlays(totPlays, team, opp):
	oppPlays = sum([int(x) for x in totPlays[opp].split(",")])
	plays = 0
	for idx, o in enumerate(get_opponents(team)):
		if idx >= CURR_WEEK:
			break
		if o == "BYE":
			continue
		plays += int(totPlays[o].split(",")[idx])

	return plays, oppPlays

def tacklesAnalysis():
	with open(f"{prefix}static/profootballreference/teams.json") as fh:
		teams = json.load(fh)

	res = {}
	for fullTeam in teams:
		team = fullTeam.split("/")[-2]
		res[team] = {}
		for idx, opp in enumerate(get_opponents(team)):
			if opp == "BYE":
				continue
			wk = idx+1
			res[team][wk] = {"dbs": 0, "lbs": 0}

			with open(f"{prefix}static/profootballreference/{opp}/stats.json") as fh:
				stats = json.load(fh)

			with open(f"{prefix}static/profootballreference/{opp}/roster.json") as fh:
				roster = json.load(fh)

			for player in stats:
				if player not in roster:
					continue
				pos = roster[player]

				if pos not in ["LB", "S", "SS", "FS", "CB", "DE", "DB", "DT", "NT"]:
					continue

				if f"wk{wk}" not in stats[player]:
					continue

				tackles = stats[player][f"wk{wk}"].get("tackles_combined", 0)
				if pos in ["LB", "DE", "DT", "NT"]:
					res[team][wk]["lbs"] += tackles
				else:
					res[team][wk]["dbs"] += tackles

	print(res["rav"])


def getDefPropsData(teams):
	pastPropData = {}
	if 0:
		for file in glob.glob(f"{prefix}static/props/wk*_def.json"):
			wk = int(file.split("wk")[-1].split("_")[0])
			if wk <= CURR_WEEK:
				with open(file) as fh:
					data = json.load(fh)
				for name in data:
					if name not in pastPropData:
						pastPropData[name] = {}
					if not data[name]["line"]:
						continue
					pastPropData[name][wk] = data[name]["line"][1:]

	with open(f"{prefix}static/props/wk{CURR_WEEK+1}_def.json") as fh:
		propData = json.load(fh)
	with open(f"{prefix}static/tot_plays.json") as fh:
		playsData = json.load(fh)

	with open(f"{prefix}static/runPassTotals.json") as fh:
		runPassData = json.load(fh)

	with open(f"{prefix}static/profootballreference/rankings.json") as fh:
		rankings = json.load(fh)
	with open(f"{prefix}static/profootballreference/averages.json") as fh:
		averages = json.load(fh)
	with open(f"{prefix}static/profootballreference/roster.json") as fh:
		roster = json.load(fh)
	with open(f"{prefix}static/profootballreference/totals.json") as fh:
		totals = json.load(fh)
	with open(f"{prefix}static/profootballreference/lastYearStats.json") as fh:
		lastYearStats = json.load(fh)

	#tacklesAnalysis()

	res = []
	for team in propData:
		for name in propData[team]:
			for prop in propData[team][name]:
				espnTeam = team

				if teams and team not in teams:
					continue

				opponents = get_opponents(espnTeam)
				opp = opponents[CURR_WEEK]
				if opp == "BYE":
					continue
				
				pos = "-"
				if name in roster[team]:
					pos = roster[team][name]

				#totPlays, oppTotPlays = getOppTotPlays(playsData, pff_team, opp)
				line = propData[team][name][prop]["line"]
				if line:
					line = line[1:]


				lastTotalOver = lastTotalGames = 0
				if line and name in lastYearStats[espnTeam] and lastYearStats[espnTeam][name]:
					for dt in lastYearStats[espnTeam][name]:
						lastTotalGames += 1
						val = 0
						if "tackles_combined" in lastYearStats[espnTeam][name][dt]:
							val = lastYearStats[espnTeam][name][dt]["tackles_combined"]
						if val > float(line):
							lastTotalOver += 1
				if lastTotalGames:
					lastTotalOver = round((lastTotalOver / lastTotalGames) * 100)

				playerStats = {}
				last5 = []
				last5WithLines = []
				totTackles = 0
				totTeamTackles = 0
				avg = 0
				totalOver = 0
				gamesPlayed = totals[espnTeam][name]["gamesPlayed"]
				totTeamSnaps = totSnaps = 0
				wks = glob.glob(f"{prefix}static/profootballreference/{espnTeam}/wk*.json")
				for wk in sorted(wks, key=lambda k: int(k.split("/")[-1][2:-5]), reverse=True):
					with open(wk) as fh:
						data = json.load(fh)
					if name not in data:
						continue

					week = int(wk.split("/")[-1][2:-5])
					tackles = data[name].get("tackles_combined", 0)
					totTackles += tackles
					if line and tackles > float(line):
						totalOver += 1

					t = str(int(tackles))
					last5.append(t)
					if name+" "+team.upper() in pastPropData and week in pastPropData[name+" "+team.upper()]:
						t += f"({pastPropData[name+' '+team.upper()][week]})"
					last5WithLines.append(t)

				if gamesPlayed:
					avg = round(totTackles / gamesPlayed, 1)
					totalOver = round((totalOver / gamesPlayed) * 100)

				overOdds = underOdds = float('-inf')
				for book in propData[team][name][prop]:
					if book == "line" or not propData[team][name][prop][book]["over"]:
						continue

					line = propData[team][name][prop]["line"][1:]
					over = propData[team][name][prop][book]["over"]
					overLine = over.split(" ")[0][1:]
					overOdd = int(over.split(" ")[1][1:-1])
					if overLine == line and overOdd > overOdds:
						overOdds = overOdd

					under = propData[team][name][prop][book]["under"]
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

				rank = oppRank = ""
				if "tpg" in rankings[espnTeam] and "otpg" in rankings[opp]:
					rank = rankings[espnTeam]["tpg"]["rank"]
					oppRank = rankings[opp]["otpg"]["rank"]

				res.append({
					"player": name.title(),
					"team": getYahooTeam(team),
					"opponent": TEAM_TRANS.get(opp, opp),
					"hit": True,
					"pos": pos,
					"rank": rank,
					"oppRank": oppRank,
					"avg": avg,
					"totalOver": totalOver,
					"lastTotalOver": lastTotalOver,
					"last5": ",".join(last5),
					"last5WithLines": ",".join(last5WithLines),
					"propType": "tackles_combined",
					"line": line or "-",
					"overOdds": overOdds,
					"underOdds": underOdds
				})
	return res

def customPropData(propData):
	pass

@props_blueprint.route('/getDefProps')
def getDefProps_route():
	teams = request.args.get("teams") or ""
	if teams:
		teams = teams.lower().split(",")
	return jsonify(getDefPropsData(teams))

def checkTrades(player, team, stats, totals):
	with open(f"{prefix}static/nfl_trades.json") as fh:
		trades = json.load(fh)

	if player not in totals[team]:
		return 0
	totGames = totals[team][player]["gamesPlayed"]

	if player not in trades:
		return totGames
	trade = trades[player]

	totGames += totals[trade["from"]][player]["gamesPlayed"]

	for file in glob.glob(f"{prefix}static/profootballreference/{trade['from']}/*.json"):
		with open(file) as fh:
			oldStats = json.load(fh)
		wk = file.split("/")[-1][:-5]
		if player in oldStats:
			stats[wk] = oldStats[player]

	return totGames

@props_blueprint.route('/getProps')
def getProps_route():
	res = []

	teams = request.args.get("teams") or ""
	if teams:
		teams = teams.upper().split(",")

	with open(f"{prefix}static/props.json") as fh:
		propData = json.load(fh)
	with open(f"{prefix}static/profootballreference/rankings.json") as fh:
		rankings = json.load(fh)
	with open(f"{prefix}static/profootballreference/totals.json") as fh:
		totals = json.load(fh)
	with open(f"{prefix}static/profootballreference/lastYearStats.json") as fh:
		lastYearStats = json.load(fh)
	with open(f"{prefix}static/profootballreference/averages.json") as fh:
		averages = json.load(fh)
	with open(f"{prefix}static/profootballreference/roster.json") as fh:
		roster = json.load(fh)
	with open(f"{prefix}static/profootballreference/schedule.json") as fh:
		schedule = json.load(fh)

	translations = {}
	for team in roster:
		for player in roster[team]:
			first = player[0].upper()
			rest = " ".join(player.title().split(" ")[1:])
			n = f"{first}. {rest}"
			translations[f"{n} {team}"] = player
			if n.split(" ")[-1].lower() in ["i", "ii", "iii", "iv", "v"]:
				n = " ".join(n.split(" ")[:-1])
				translations[f"{n} {team}"] = player
	#customPropData(propData)
	player = ""

	for nameRow in propData:
		name = " ".join(nameRow.split(" ")[:-1])
		team = nameRow.split(" ")[-1]
		espnTeam = getYahooTeam(team.lower())
		opp = get_opponents(espnTeam)[CURR_WEEK]

		if team == "team":
			continue

		if teams and team not in teams:
			continue

		name = name.replace("-", " ")
		if name == "T. Etienne":
			name = "T. Etienne Jr"
		elif name == "D. Henderson":
			name = "D. Henderson Jr"
		elif name == "A. St. Brown":
			name = "A. Ra St Brown"

		pos = "-"
		playerStats = {}
		totGames = 0

		if name+" "+espnTeam not in translations:
			#print(name)
			player = name
		else:
			player = translations[name+" "+espnTeam]
			player = player.replace(".", "")
			if player == "jameson williams" and espnTeam == "det":
				player = "jamaal williams"
			elif player == "marcus jones":
				player = "mac jones"
			for file in os.listdir(f"{prefix}static/profootballreference/{espnTeam}/"):
				with open(f"{prefix}static/profootballreference/{espnTeam}/{file}") as fh:
					gameStats = json.load(fh)
				wk = file.split("/")[-1][:-5]
				if player in gameStats:
					playerStats[wk] = gameStats[player]
			totGames = checkTrades(player, team.lower(),playerStats, totals)

		for typ in propData[nameRow]:
			overOdds = propData[nameRow][typ]["sideOneOdds"]
			underOdds = propData[nameRow][typ]["sideTwoOdds"]
			if not overOdds.startswith("-"):
				overOdds = "+"+overOdds
			if not underOdds.startswith("-"):
				underOdds = "+"+underOdds

			line = propData[nameRow][typ]["line"]
			if line:
				pass
				#diff = abs(proj - float(line))

			lastTotalOver = lastTotalGames = 0
			if line and player in lastYearStats[espnTeam] and lastYearStats[espnTeam][player]:
				for dt in lastYearStats[espnTeam][player]:
					lastTotalGames += 1
					val = 0
					if typ == "rush_recv_yd":
						val = lastYearStats[espnTeam][player][dt].get("rush_yds", 0) + lastYearStats[espnTeam][player][dt].get("rec_yds", 0)
					else:
						t = typ.replace("comp", "cmp").replace("_yd", "_yds").replace("recv_rec", "rec").replace("recv_", "rec_")
						if t in lastYearStats[espnTeam][player][dt]:
							val = lastYearStats[espnTeam][player][dt][t]
					if val > float(line):
						lastTotalOver += 1
			if lastTotalGames:
				lastTotalOver = round((lastTotalOver / lastTotalGames) * 100)

			last5 = []
			tot = totalOver = totalOverLast3 = 0
			for wk in sorted(playerStats.keys(), key=lambda k: int(k[2:]), reverse=True):
				if typ == "rush_recv_yd":
					val = playerStats[wk].get("rush_yds", 0) + playerStats[wk].get("rec_yds", 0)
					last5.append(val)
					tot += val
					if val > float(line):
						totalOver += 1
						if len(last5) <= 3:
							totalOverLast3 += 1
				else:
					t = typ.replace("comp", "cmp").replace("_yd", "_yds").replace("recv_rec", "rec").replace("recv_", "rec_")
					val = playerStats[wk].get(t, 0)
					tot += val
					last5.append(val)
					if val > float(line):
						totalOver += 1
						if len(last5) <= 3:
							totalOverLast3 += 1

			diff = 0
			if line and totGames:
				avg = tot / totGames
				diff = round((avg / float(line) - 1), 2)
			if totalOver and totGames:
				totalOver = round((totalOver / totGames) * 100)
				last5Size = len(last5) if len(last5) < 3 else 3
				totalOverLast3 = round((totalOverLast3 / last5Size) * 100)

			avg = 0
			if totGames:
				avg = round(tot / totGames, 1)

			lastAvg = 0
			if player in averages[espnTeam] and averages[espnTeam][player]:
				if typ == "rush_recv_yd":
					if "rush_yds" in averages[espnTeam][player] and "rec_yds" in averages[espnTeam][player]:
						lastAvg = averages[espnTeam][player]["rush_yds"] + averages[espnTeam][player]["rec_yds"]
				else:
					t = typ.replace("comp", "cmp").replace("_yd", "_yds").replace("recv_rec", "rec").replace("recv_", "rec_")
					if t in averages[espnTeam][player]:
						lastAvg = averages[espnTeam][player][t]
				lastAvg = round(lastAvg, 1)

			oppRank = ""
			oppRankVal = ""
			rankingsProp = convertRankingsProp(typ)
			if opp != "BYE" and "o"+rankingsProp in rankings[opp]:
				oppRankVal = str(rankings[opp]["o"+rankingsProp]["season"])
				oppRank = rankings[opp]['o'+rankingsProp]['rank']
			#print(player)
			res.append({
				"player": player.title(),
				"team": espnTeam.upper(),
				"opponent": opp.upper(),
				"oppRank": oppRank,
				"hit": True,
				"pos": pos,
				"lastAvg": lastAvg,
				"avg": avg,
				"last5": last5,
				"diff": diff,
				"totalOver": totalOver,
				"totalOverLast3": totalOverLast3,
				"lastTotalOver": lastTotalOver,
				"propType": typ,
				"line": line or "-",
				"overOdds": overOdds,
				"underOdds": underOdds,
				"stats": playerStats
			})

	teamTotals(schedule)
	return jsonify(res)

def getTeamTds(schedule):
	teamTds = {}
	wk = f"wk{CURR_WEEK+1}"
	for file in os.listdir(f"{prefix}static/profootballreference/"):
		if file.endswith("json"):
			continue
		team = file.split("/")[-1]
		wks = glob.glob(f"{prefix}static/profootballreference/{team}/wk*.json")
		for wk in sorted(wks, key=lambda k: int(k.split("/")[-1][2:-5]), reverse=True):
			with open(wk) as fh:
				stats = json.load(fh)

			week = int(wk.split("/")[-1][2:-5])
			opp = ""
			for games in schedule[f"wk{week}"]:
				if team in games.split(" @ "):
					opp = games.replace(team, "").replace(" @ ", "")
					break

			tds = 0
			for player in stats:
				tds += stats[player].get("pass_td", 0) + stats[player].get("rush_td", 0) + stats[player].get("def_td", 0) + stats[player].get("def_int_td", 0)

			if team not in teamTds:
				teamTds[team] = {"scored": [], "allowed": [0]*CURR_WEEK}
			if opp not in teamTds:
				teamTds[opp] = {"scored": [], "allowed": [0]*CURR_WEEK}
			teamTds[team]["scored"].append(int(tds))
			teamTds[opp]["allowed"][week-1] = int(tds)

	return teamTds


def teamTotals(schedule):
	with open(f"{prefix}static/profootballreference/scores.json") as fh:
		scores = json.load(fh)
	teamTds = getTeamTds(schedule)
	totals = {}
	for wk in scores:
		games = schedule[wk]
		for team in scores[wk]:
			opp = ""
			for game in games:
				if team in game.split(" @ "):
					opp = game.replace(team, "").replace(" @ ", "")
			if team not in totals:
				totals[team] = {"ppg": 0, "ppga": 0, "games": 0, "overs": [], "ttOvers": []}
			if opp not in totals:
				totals[opp] = {"ppg": 0, "ppga": 0, "games": 0, "overs": [], "ttOvers": []}
			totals[team]["games"] += 1
			totals[team]["ppg"] += scores[wk][team]
			totals[team]["ppga"] += scores[wk][opp]
			totals[team]["ttOvers"].append(str(scores[wk][team]))
			totals[team]["overs"].append(str(scores[wk][team] + scores[wk][opp]))

	out = "\t".join([x.upper() for x in ["team", "ppg", "ppga", "overs", "overs avg", "tt overs", "tt avg", "tot tds", "tot tds avg", "tot tds allowed", "tot tds allowed avg"]])
	out += "\n"
	#out += ":--|:--|:--|:--|:--|:--|:--\n"
	cutoff = 20
	for game in schedule[f"wk{CURR_WEEK+1}"]:
		away, home = map(str, game.split(" @ "))
		ppg = round(totals[away]["ppg"] / totals[away]["games"], 1)
		ppga = round(totals[away]["ppga"] / totals[away]["games"], 1)
		overs = ",".join(totals[away]["overs"][:cutoff])
		oversAvg = round(sum([int(x) for x in totals[away]["overs"]]) / len(totals[away]["overs"]), 1)
		ttOvers = ",".join(totals[away]["ttOvers"][:cutoff])
		ttOversAvg = round(sum([int(x) for x in totals[away]["ttOvers"]]) / len(totals[away]["ttOvers"]), 1)
		totTds = ",".join([str(x) for x in teamTds[away]["scored"]])
		totTdsAvg = round(sum(teamTds[away]["scored"]) / len(teamTds[away]["scored"]), 1)
		totTdsAllowed = ",".join([str(x) for x in teamTds[away]["allowed"][::-1]])
		totTdsAllowedAvg = round(sum(teamTds[away]["allowed"]) / len(teamTds[away]["allowed"]), 1)
		out += "\t".join([away.upper(), str(ppg), str(ppga), overs, str(oversAvg), ttOvers, str(ttOversAvg), totTds, str(totTdsAvg), totTdsAllowed, str(totTdsAllowedAvg)]) + "\n"
		ppg = round(totals[home]["ppg"] / totals[home]["games"], 1)
		ppga = round(totals[home]["ppga"] / totals[home]["games"], 1)
		overs = ",".join(totals[home]["overs"][:cutoff])
		oversAvg = round(sum([int(x) for x in totals[home]["overs"]]) / len(totals[home]["overs"]), 1)
		ttOvers = ",".join(totals[home]["ttOvers"][:cutoff])
		ttOversAvg = round(sum([int(x) for x in totals[home]["ttOvers"]]) / len(totals[home]["ttOvers"]), 1)
		totTds = ",".join([str(x) for x in teamTds[home]["scored"]])
		totTdsAvg = round(sum(teamTds[home]["scored"]) / len(teamTds[home]["scored"]), 1)
		totTdsAllowed = ",".join([str(x) for x in teamTds[home]["allowed"][::-1]])
		totTdsAllowedAvg = round(sum(teamTds[home]["allowed"]) / len(teamTds[home]["allowed"]), 1)
		out += "\t".join([home.upper(), str(ppg), str(ppga), overs, str(oversAvg), ttOvers, str(ttOversAvg), totTds, str(totTdsAvg), totTdsAllowed, str(totTdsAllowedAvg)]) + "\n"
		out += "\t".join(["-"]*11) + "\n"

	with open(f"{prefix}static/props/totals.csv", "w") as fh:
		fh.write(out)

def convertRankingsProp(prop):
	if "+" in prop:
		return prop
	elif prop in ["pass_comp", "recv_rec"]:
		return "cmppg"
	elif prop in ["pass_yd", "recv_yd"]:
		return "paydpg"
	elif prop in ["rush_yd"]:
		return "ydpra"
	elif prop in ["rush_att"]:
		return "ruattpg"
	elif prop in ["pass_att"]:
		return "paattpg"
	elif prop == "pass_td":
		return "patdpg"
	elif prop == "pass_int":
		return "intpg"
	#return prop[0]+"pg"
	return prop

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
	teams = request.args.get("teams") or ""
	return render_template("props.html", curr_week=CURR_WEEK, teams=teams)

@props_blueprint.route('/defprops')
def props_def_route():
	teams = request.args.get("teams") or ""
	return render_template("defprops.html", curr_week=CURR_WEEK, teams=teams)

def writeDefProps(week):
	actionNetworkBookIds = {
		68: "draftkings",
		69: "fanduel",
		1599: "betmgm"
	}
	prop = "tackles_combined"
	props = {}
	optionTypes = {}

	date = datetime.now()
	date = str(date)[:10]

	path = f"{prefix}static/props/wk{week+1}defprops.json"
	url = f"https://api.actionnetwork.com/web/v1/leagues/1/props/core_bet_type_70_tackles_assists?bookIds=69,68,1599&date={date.replace('-', '')}"
	os.system(f"curl -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:106.0) Gecko/20100101 Firefox/106.0' -k \"{url}\" -o {path}")

	with open(path) as fh:
		j = json.load(fh)

	with open(path, "w") as fh:
		json.dump(j, fh, indent=4)

	if "markets" not in j:
		return
	market = j["markets"][0]

	for option in market["rules"]["options"]:
		optionTypes[int(option)] = market["rules"]["options"][option]["option_type"].lower()

	teamIds = {}
	for row in market["teams"]:
		teamIds[row["id"]] = row["abbr"].lower()

	playerIds = {}
	for row in market["players"]:
		playerIds[row["id"]] = row["full_name"].lower().replace(".", "").replace("-", " ").replace("'", "")

	books = market["books"]
	for bookData in books:
		bookId = bookData["book_id"]
		if bookId not in actionNetworkBookIds:
			continue
		for oddData in bookData["odds"]:
			player = playerIds[oddData["player_id"]]
			if player == "lawrence guy sr":
				player = "lawrence guy"
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

	with open(f"{prefix}static/props/wk{week+1}_def.json", "w") as fh:
		json.dump(props, fh, indent=4)

def fixLines(propData):
	pass

def writeProps():
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

		team = getYahooTeam(currProps["team"].lower())
		player = currProps["player"].lower().title().replace("Jr.", "Jr")
		player += " "+team.upper()
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
		writeProps()
		writeDefProps(week)