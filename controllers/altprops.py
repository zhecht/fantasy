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

altprops_blueprint = Blueprint('altprops', __name__, template_folder='views')

prefix = ""
if os.path.exists("/home/zhecht/fantasy"):
	prefix = "/home/zhecht/fantasy/"

@altprops_blueprint.route('/getAltProps')
def getProps_route():
	with open(f"{prefix}static/nbaprops/customProps.json") as fh:
		propData = json.load(fh)
	with open(f"{prefix}static/basketballreference/schedule.json") as fh:
		schedule = json.load(fh)
	with open(f"{prefix}static/basketballreference/totals.json") as fh:
		totals = json.load(fh)
	with open(f"{prefix}static/basketballreference/averages.json") as fh:
		averages = json.load(fh)
	with open(f"{prefix}static/basketballreference/lastYearStats.json") as fh:
		lastYearStats = json.load(fh)

	date = datetime.now()
	date = str(date)[:10]

	data = []
	for game in schedule[date]:
		for team in game.split(" @ "):

			for player in propData[team]:
				avgMin = 0
				if player in totals[team] and totals[team][player]["gamesPlayed"]:
					avgMin = int(totals[team][player]["min"] / totals[team][player]["gamesPlayed"])

				for prop in propData[team][player]:
					lines = propData[team][player][prop]["line"]
					odds = propData[team][player][prop]["odds"]
					isOver = True

					avg = 0.0
					if player in totals[team] and totals[team][player]["gamesPlayed"]:
						val = 0
						if "+" in prop:
							for p in prop.split("+"):
								val += totals[team][player][p]
						elif prop in totals[team][player]:
							val = totals[team][player][prop]
						avg = round(val / totals[team][player]["gamesPlayed"], 1)
					lastAvg = 0
					if player in averages[team]:
						if "+" in prop:
							for p in prop.split("+"):
								lastAvg += averages[team][player][p]
						elif prop in averages[team][player]:
							lastAvg = averages[team][player][prop]
						lastAvg = round(lastAvg, 1)

					for idx, line in enumerate(lines):
						if idx == 1:
							isOver = False
						odd = odds[idx]
						line = float(line[1:])

						lastTotOver = lastTotGames = 0
						if player in lastYearStats[team]:
							for dt in lastYearStats[team][player]:
								minutes = lastYearStats[team][player][dt]["min"]
								if minutes:
									lastTotGames += 1
									val = 0.0
									if "+" in prop:
										for p in prop.split("+"):
											val += lastYearStats[team][player][dt][p]
									else:
										val = lastYearStats[team][player][dt][prop]
									valPerMin = float(val / minutes)
									linePerMin = line / avgMin
									if valPerMin >= linePerMin:
										lastTotOver += 1
						if lastTotGames:
							lastTotOver = round((lastTotOver / lastTotGames) * 100)

						totalOver = totalGames = 0
						last5 = []
						if avgMin:
							files = sorted(glob.glob(f"{prefix}static/basketballreference/{team}/*.json"), key=lambda k: datetime.strptime(k.split("/")[-1].replace(".json", ""), "%Y-%m-%d"), reverse=True)
							for file in files:
								with open(file) as fh:
									gameStats = json.load(fh)
								if player in gameStats:
									minutes = gameStats[player]["min"]
									if minutes > 0:
										totalGames += 1
										val = 0.0
										if "+" in prop:
											for p in prop.split("+"):
												val += gameStats[player][p]
										else:
											val = gameStats[player][prop]

										if len(last5) < 7:
											last5.append(str(int(val)))
										valPerMin = float(val / minutes)
										linePerMin = float(line) / avgMin
										#if valPerMin > linePerMin:
										if val > float(line):
											totalOver += 1
						if totalGames:
							totalOver = round((totalOver / totalGames) * 100)

						data.append({
							"player": player.title(),
							"team": team.upper(),
							"game": game,
							"propType": prop,
							"isOver": isOver,
							"line": line,
							"avg": avg,
							"odds": odd,
							"lastAvg": lastAvg,
							"avgMin": avgMin,
							"totalOver": totalOver,
							"lastTotalOver": lastTotOver,
							"last5": ",".join(last5)
						})
	return jsonify(data)

@altprops_blueprint.route('/altprops')
def props_route():
	return render_template("altprops.html")
