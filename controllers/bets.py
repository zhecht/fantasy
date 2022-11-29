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
	with open(f"{prefix}static/basketballreference/boxscores.json") as fh:
		boxscores = json.load(fh)

	teams = []
	for bet in bets["bets"]:
		teams.extend(bet["players"].keys())

	finished = []
	finished = ["atl @ phi", "min @ wsh", "cha @ bos", "orl @ bkn", "cle @ tor", "chi @ utah", "hou @ den", "phx @ sac", "ind @ lal"]

	allStats = {}
	if not res:
		res = {"scores": {}, "timeLeft": {}}
	for game in boxscores[date]:
		away, home = map(str, game.split(" @ "))

		if away not in allStats:
			allStats[away] = {}
		if home not in allStats:
			allStats[home] = {}

		if away not in teams and home not in teams:
			continue

		#t = soup.find("div", class_="Gamestrip__Overview").find("div", class_="ScoreCell__Time").text.strip()
		if "all" in finished or game in finished:
			res["timeLeft"][away] = "final"
			res["timeLeft"][home] = "final"
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
		for idx, table in enumerate(soup.findAll("table")[1:5]):
			if idx == 2:
				playerList = []
				team = home

			playerIdx = 0
			for row in table.findAll("tr")[:-2]:
				if idx == 0 or idx == 2:
					# PLAYERS
					if row.text.strip().lower() in ["starters", "bench", "team"]:
						continue
					nameLink = row.find("a").get("href").split("/")
					fullName = nameLink[-1].replace("-", " ")
					playerList.append(fullName)
				else:
					# idx==1 or 3. STATS
					if row.find("td").text.strip().lower() == "min":
						headers = []
						for td in row.findAll("td"):
							headers.append(td.text.strip().lower())
						continue

					player = playerList[playerIdx]
					playerIdx += 1
					playerStats = {}
					for tdIdx, td in enumerate(row.findAll("td")):
						if td.text.lower().startswith("dnp-") or td.text.lower().startswith("has not"):
							playerStats["min"] = 0
							break
						header = headers[tdIdx]
						if td.text.strip().replace("-", "") == "":
							playerStats[header] = 0
						elif header in ["fg", "3pt", "ft"]:
							made, att = map(int, td.text.strip().split("-"))
							playerStats[header+"a"] = att
							playerStats[header+"m"] = made
						else:
							val = int(td.text.strip())
							playerStats[header] = val

					allStats[team][player] = playerStats

	for bet in bets["bets"]:
		for team in bet["players"]:
			fin = False
			for f in finished:
				if team in f.split(" @ "):
					fin = True
			if fin:
				continue
			if team not in res["scores"]:
				res["scores"][team] = {}
			for player in bet["players"][team]:
				player, prop = map(str, player.split("\t"))
				propVal = int(prop.split(" ")[0].replace("+", "").replace("u", ""))
				prop = prop.split(" ")[1]
				if player not in res["scores"][team]:
					res["scores"][team][player] = {}
				if player not in allStats[team]:
					res["scores"][team][player][prop] = 0
				else:
					res["scores"][team][player][prop] = allStats[team][player].get(prop, 0)

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