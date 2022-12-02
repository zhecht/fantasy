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

bets_blueprint = Blueprint('bets', __name__, template_folder='views')

prefix = ""
if os.path.exists("/home/zhecht/fantasy"):
	# if on linux aka prod
	prefix = "/home/zhecht/fantasy/"

@bets_blueprint.route('/updatebets', methods=["POST"])
def bets_post_route():
	date = request.args.get("date")
	with open(f"{prefix}static/nbaprops/bets.json") as fh:
		bets = json.load(fh)
	with open(f"{prefix}static/nbaprops/settled.json") as fh:
		res = json.load(fh)

	if not res:
		res = {
			"nba": {"scores": {}, "timeLeft": {}},
			"nhl": {"scores": {}, "timeLeft": {}}
		}

	paths = ["basketball", "hockey"]
	allStats = {}
	for idx, sport in enumerate(["nba", "nhl"]):
		with open(f"{prefix}static/{paths[idx]}reference/boxscores.json") as fh:
			boxscores = json.load(fh)
		teams = []
		for bet in bets["bets"]:
			if bet["sport"] != sport:
				continue
			teams.extend(bet["players"].keys())

		finished = ["phi @ cle", "atl @ orl", "phi @ cle", "sj @ tor", "nyr @ ott", "mil @ ny", "wsh @ bkn", "tor @ no", "sa @ okc", "mem @ min", "hou @ den", "chi @ phx", "lac @ utah", "ind @ sac", "por @ lal", "buf @ det", "edm @ chi"]

		allStats[sport] = {}
		for game in boxscores[date]:
			away, home = map(str, game.split(" @ "))

			if away not in allStats[sport]:
				allStats[sport][away] = {}
			if home not in allStats[sport]:
				allStats[sport][home] = {}

			if away not in teams and home not in teams:
				continue

			if "all" in finished or game in finished:
				res[sport]["timeLeft"][away] = "final"
				res[sport]["timeLeft"][home] = "final"
				continue

			link = boxscores[date][game].replace("game?gameId=", "boxscore/_/gameId/")
			url = f"https://www.espn.com{link}"
			outfile = "out"
			time.sleep(0.2)
			call(["curl", "-k", url, "-o", outfile])
			soup = BS(open(outfile, 'rb').read(), "lxml")

			headers = []
			playerList = []
			team = away
			endCutoff = 5 if sport == "nba" else 9
			for tableIdx, table in enumerate(soup.findAll("table")[1:endCutoff]):
				if sport == "nba":
					if tableIdx == 2:
						playerList = []
						team = home
				elif sport == "nhl":
					if tableIdx in [2,4,6]:
						playerList = []
					if tableIdx == 4:
						team = home

				playerIdx = 0
				for row in table.findAll("tr")[:-2]:
					arr = [0,2] if sport == "nba" else [0,2,4,6]
					if tableIdx in arr:
						# PLAYERS
						if row.text.strip().lower() in ["starters", "bench", "team", "skaters", "defensemen", "goalies"]:
							continue
						if not row.find("a"):
							continue
						nameLink = row.find("a").get("href").split("/")
						if sport == "nba":
							fullName = nameLink[-1].replace("-", " ")
						else:
							fullName = row.find("a").text.lower().title().replace("-", " ")
							if fullName.startswith("J.T."):
								fullName = fullName.replace("J.T.", "J.")
							elif fullName.startswith("J.J."):
								fullName = fullName.replace("J.J.", "J.")
							elif fullName.startswith("T.J."):
								fullName = fullName.replace("T.J.", "T.")
							elif fullName.startswith("A.J."):
								fullName = fullName.replace("A.J.", "A.")
						playerList.append(fullName)
					else:
						# idx==1 or 3. STATS
						if not row.find("td"):
							continue
						firstTd = row.find("td").text.strip().lower()
						if firstTd in ["min", "g", "sa"]:
							headers = []
							for td in row.findAll("td"):
								headers.append(td.text.strip().lower())
							continue

						try:
							player = playerList[playerIdx]
						except:
							continue
						playerIdx += 1
						playerStats = {}
						for tdIdx, td in enumerate(row.findAll("td")):
							if td.text.lower().startswith("dnp-") or td.text.lower().startswith("has not"):
								playerStats["min"] = 0
								break
							header = headers[tdIdx]
							if sport == "nba":
								if td.text.strip().replace("-", "") == "":
									playerStats[header] = 0
								elif header in ["fg", "3pt", "ft"]:
									made, att = map(int, td.text.strip().split("-"))
									playerStats[header+"a"] = att
									playerStats[header+"m"] = made
								else:
									val = int(td.text.strip())
									playerStats[header] = val
							else:
								val = 0
								if header in ["toi", "pptoi", "shtoi", "estoi"]:
									valSp = td.text.strip().split(":")
									val = int(valSp[0])+round(int(valSp[1]) / 60, 2)
								else:
									val = float(td.text.strip())
								playerStats[header] = val

						allStats[sport][team][player] = playerStats

	for bet in bets["bets"]:
		sport = bet["sport"]
		for team in bet["players"]:
			fin = False
			for f in finished:
				if team in f.split(" @ "):
					fin = True
			if fin:
				continue
			if team not in res[sport]["scores"]:
				res[sport]["scores"][team] = {}
			for player in bet["players"][team]:
				player, prop = map(str, player.split("\t"))
				propVal = int(prop.split(" ")[0].replace("+", "").replace("u", ""))
				statsPlayer = player
				playerSp = player.split(" ")
				if sport == "nhl":
					statsPlayer = playerSp[0][0].upper()+". "+playerSp[1].title()

				prop = prop.split(" ")[1]
				if player not in res[sport]["scores"][team]:
					res[sport]["scores"][team][player] = {}
				if statsPlayer not in allStats[sport][team]:
					res[sport]["scores"][team][player][prop] = 0
				else:
					if sport == "nhl":
						res[sport]["scores"][team][player]["sog"] = allStats[sport][team][statsPlayer].get("s", 0)
						res[sport]["scores"][team][player]["pts"] = allStats[sport][team][statsPlayer].get("g", 0)+allStats[sport][team][statsPlayer].get("a", 0)
					else:
						res[sport]["scores"][team][player][prop] = allStats[sport][team][statsPlayer].get(prop, 0)

	with open(f"{prefix}static/nbaprops/settled.json", "w") as fh:
		json.dump(res, fh, indent=4)

	return jsonify(res)

@bets_blueprint.route('/bets')
def bets_route():
	with open(f"{prefix}static/nbaprops/bets.json") as fh:
		bets = json.load(fh)
	res = bets["bets"]
	for bet in res:
		if bet["odds"] > 0:
			bet["odds"] = f"+{bet['odds']}"
		else:
			bet["odds"] = str(bet["odds"])

	date = datetime.now()
	date = str(date)[:10]
	if request.args.get("date"):
		date = request.args.get("date")

	return render_template("bets.html", bets=res, date=date)