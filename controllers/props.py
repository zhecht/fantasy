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
	elif team == "SDG":
		return "LAC"
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


def getDefPropsData():
	pastPropData = {}
	for file in glob.glob(f"{prefix}static/props/wk*.json"):
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

	#tacklesAnalysis()

	res = []
	for nameRow in propData:
		name = " ".join(nameRow.split(" ")[:-1])
		name = fixName(name.lower())
		team = nameRow.split(" ")[-1]

		if team not in ["PHI", "WSH"]:
			#continue
			pass

		opp = get_opponents(getProfootballReferenceTeam(team.lower()))[CURR_WEEK]
		pff_team = getProfootballReferenceTeam(team.lower())

		if opp == "BYE":
			continue

		with open(f"{prefix}static/profootballreference/{pff_team}/stats.json") as fh:
			stats = json.load(fh)

		with open(f"{prefix}static/profootballreference/{pff_team}/roster.json") as fh:
			roster = json.load(fh)
		
		pos = "-"
		if name in roster:
			pos = roster[name]

		totPlays, oppTotPlays = getOppTotPlays(playsData, pff_team, opp)
		opponents = get_opponents(pff_team)

		line = propData[nameRow]["line"]
		if line:
			line = line[1:]

		playerStats = {}
		last5 = []
		last5WithLines = []
		totTackles = 0
		totTeamTackles = 0
		avgSnaps = 0
		lastSnaps = 0
		avg = 0
		totalOver = 0
		if name not in stats:
			pass
		else:
			gameLogs = stats[name]
			gamesPlayed = 0
			totTeamSnaps = totSnaps = 0
			for wk in sorted(gameLogs.keys(), reverse=True):
				if wk == "tot" or not gameLogs[wk].get("snap_counts", 0):
					continue
				gamesPlayed += 1
				totTeamSnaps += int(gameLogs[wk]["snap_counts"] / (gameLogs[wk]["snap_perc"] / 100))
				totSnaps += gameLogs[wk]["snap_counts"]
				if lastSnaps == 0:
					lastSnaps = gameLogs[wk]["snap_perc"]

				week = int(wk[2:])
				totTeamTackles += stats["DEF"][wk]["tackles"]
				tackles = gameLogs[wk].get("tackles_combined", 0)
				totTackles += tackles
				if line and tackles > float(line):
					totalOver += 1

				if "tackles_combined" in gameLogs[wk]:
					t = str(gameLogs[wk]["tackles_combined"])
					last5.append(t)
					if name+" "+team in pastPropData and week in pastPropData[name+" "+team]:
						t += f"({pastPropData[name+' '+team][week]})"
					last5WithLines.append(t)

			if gamesPlayed:
				avg = round(totTackles / gamesPlayed, 1)
				totalOver = round((totalOver / gamesPlayed) * 100)
			playerStats = gameLogs
			playerStats["tot"]["gamesPlayed"] = gamesPlayed
			if totTeamSnaps:
				avgSnaps = int(round((totSnaps / totTeamSnaps)*100))

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

		diff = 0

		avgTotPlays = int(round(totPlays / CURR_WEEK))
		avgOppTotPlays = int(round(oppTotPlays / CURR_WEEK))
		tackleShare = 0
		proj = 0
		if totTeamTackles:
			tackleShare = round((totTackles / totTeamTackles)*100, 1)
			proj = round((totTackles / totTeamTackles)*int(round(avgOppTotPlays+avgTotPlays) / 2), 1)

		if line:
			diff = abs(proj - float(line))

		rank = oppRank = ""
		if "tpg" in rankings[pff_team] and "otpg" in rankings[opp]:
			rank = rankings[pff_team]["tpg"]["rank"]
			oppRank = rankings[opp]["otpg"]["rank"]

		res.append({
			"player": name.title(),
			"team": getYahooTeam(team),
			"opponent": TEAM_TRANS.get(opp, opp),
			"hit": True,
			"pos": pos,
			"proj": proj,
			"diff": diff,
			"rank": rank,
			"oppRank": oppRank,
			"avg": avg,
			"totalOver": totalOver,
			"avgSnaps": f"{avgSnaps}% ({lastSnaps}%)",
			"avgTotPlays": avgTotPlays,
			"avgOppTotPlays": avgOppTotPlays,
			"oppPassPerc": f"{runPassData[opp]['passPerc']}%",
			"tackleShare": tackleShare,
			"last5": ",".join(last5),
			"last5WithLines": ",".join(last5WithLines),
			"propType": "tackles_combined",
			"line": line or "-",
			"overOdds": "over ("+overOdds+")",
			"underOdds": "under ("+underOdds+")",
			"stats": playerStats
		})
	return res

def customPropData(propData):
	pass

@props_blueprint.route('/getDefProps')
def getDefProps_route():
	return jsonify(getDefPropsData())

def checkTrades(player, stats):
	with open(f"{prefix}static/nfl_trades.json") as fh:
		trades = json.load(fh) 

	if player not in trades:
		return
	trade = trades[player]
	with open(f"{prefix}static/profootballreference/{trade['from']}/stats.json") as fh:
		oldStats = json.load(fh)
	if player in oldStats:
		for wk in oldStats[player]:
			if wk == "tot" or wk in stats:
				continue
			stats[wk] = oldStats[player][wk]

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

	customPropData(propData)

	players_on_teams,translations = read_rosters()
	fa,fa_translations = read_FA_translations()
	translations = {**translations, **fa_translations}

	for nameRow in propData:
		name = " ".join(nameRow.split(" ")[:-1])
		team = nameRow.split(" ")[-1]
		pff_team = getProfootballReferenceTeam(team.lower())
		opp = get_opponents(pff_team)[CURR_WEEK]

		if team == "team":
			continue

		with open(f"{prefix}static/profootballreference/{pff_team}/stats.json") as fh:
			stats = json.load(fh)

		if teams and team not in teams:
			continue

		if name == "T. Etienne":
			name = "T. Etienne Jr"
		if name.endswith("Jr"):
			name = name.replace("Jr", "Jr.")

		pos = "-"
		playerStats = {}
		if name+" "+getYahooTeam(team) not in translations:
			#print(name)
			player = name
		else:
			player = translations[name+" "+getYahooTeam(team)]
			player = player.replace(".", "")
			if player == "terrace marshall jr":
				player = "terrace marshall"
			elif player == "amari rodgers":
				player = "aaron rodgers"
			if player in stats:
				gameLogs = stats[player]
				checkTrades(player, gameLogs)
				gamesPlayed = 0
				for wk in sorted(gameLogs.keys(), reverse=True):
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

			line = propData[nameRow][typ]["line"]
			if line:
				pass
				#diff = abs(proj - float(line))

			last5 = []
			tot = totGames = totalOver = 0
			if player in stats:
				gameLogs = stats[player]
				checkTrades(player, gameLogs)
				for wk in sorted(gameLogs.keys(), reverse=True):
					if wk == "tot":
						continue
					if typ == "rush_recv_yd":
						if "rush_yds" in gameLogs[wk] and "rec_yds" in gameLogs[wk]:
							val = gameLogs[wk]["rush_yds"] + gameLogs[wk]["rec_yds"]
							if val > float(line):
								totalOver += 1
							last5.append(val)
							if gameLogs[wk]["snap_counts"] > 0:
								totGames += 1
								tot += val
					else:
						t = typ.replace("comp", "cmp").replace("_yd", "_yds").replace("recv_rec", "rec").replace("recv_", "rec_")
						if t in gameLogs[wk]:
							if gameLogs[wk][t] > float(line):
								totalOver += 1
							last5.append(gameLogs[wk][t])
							if gameLogs[wk]["snap_counts"] > 0:
								totGames += 1
								tot += gameLogs[wk][t]

			diff = 0
			if line and totGames:
				avg = tot / totGames
				diff = round((avg / float(line) - 1), 2)
			if totalOver and totGames:
				totalOver = round((totalOver / totGames) * 100)

			avg = 0
			if totGames:
				avg = round(tot / totGames, 1)

			oppRank = ""
			oppRankVal = ""
			rankingsProp = convertRankingsProp(typ)
			if "o"+rankingsProp in rankings[opp]:
				oppRankVal = str(rankings[opp]["o"+rankingsProp]["season"])
				oppRank = rankings[opp]['o'+rankingsProp]['rank']
			#print(player)
			res.append({
				"player": player.title(),
				"team": getYahooTeam(team),
				"opponent": getYahooTeam(TEAM_TRANS.get(opp, opp).upper()),
				"oppRank": oppRank,
				"hit": True,
				"pos": pos,
				"avg": avg,
				"last5": last5,
				"diff": diff,
				"totalOver": totalOver,
				"propType": typ,
				"line": line or "-",
				"overOdds": propData[nameRow][typ]["sideOneType"]+ " ("+overOdds+")",
				"underOdds": propData[nameRow][typ]["sideTwoType"]+ " ("+underOdds+")",
				"stats": playerStats
			})

	return jsonify(res)

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
	return render_template("defprops.html", curr_week=CURR_WEEK)

def writeDefProps(week):
	actionNetworkBookIds = {
		68: "draftkings",
		69: "fanduel"
	}
	props = {}
	optionTypes = {}

	date = datetime.now()
	date = str(date)[:10]

	path = f"{prefix}static/props/wk{week+1}defprops.json"
	url = f"https://api.actionnetwork.com/web/v1/leagues/1/props/core_bet_type_70_tackles_assists?bookIds=69,68&date={date.replace('-', '')}"
	time.sleep(0.2)
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

	with open(f"{prefix}static/props/wk{week+1}_def.json", "w") as fh:
		json.dump(props, fh, indent=4)

def fixLines(propData):
	pass

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
		player = player.replace("Jr.", "Jr")
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