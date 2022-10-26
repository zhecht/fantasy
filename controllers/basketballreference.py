import argparse
import datetime
import glob
import json
import math
import os
import operator
import re
import time

from bs4 import BeautifulSoup as BS
from bs4 import Comment
import datetime
from sys import platform
from subprocess import call
from glob import glob

try:
	from controllers.functions import *
except:
	from functions import *

try:
  import urllib2 as urllib
except:
  import urllib.request as urllib

prefix = ""
if os.path.exists("/home/zhecht/fantasy"):
	prefix = "/home/zhecht/fantasy/"

def write_stats(date):
	with open(f"{prefix}static/basketballreference/boxscores.json") as fh:
		boxscores = json.load(fh)

	with open(f"{prefix}static/basketballreference/playerIds.json") as fh:
		playerIds = json.load(fh)

	if date not in boxscores:
		print("No games found for this date")
		exit()

	allStats = {}
	for game in boxscores[date]:
		away, home = map(str, game.split(" @ "))

		if away not in allStats:
			allStats[away] = {}
		if home not in allStats:
			allStats[home] = {}

		link = boxscores[date][game].replace("game?gameId=", "boxscore/_/gameId/")
		url = f"https://www.espn.com{link}"
		outfile = "out"
		call(["curl", "-k", url, "-o", outfile])
		soup = BS(open(outfile, 'rb').read(), "lxml")
		
		# tables are split with players then stats, players -> stats
		headers = []
		playerList = []
		team = away
		for idx, table in enumerate(soup.findAll("table")[1:5]):
			if idx == 2:
				playerList = []
				team = home

			if team not in playerIds:
				playerIds[team] = {}

			playerIdx = 0
			for row in table.findAll("tr")[:-2]:
				if idx == 0 or idx == 2:
					# PLAYERS
					if row.text.strip().lower() in ["starters", "bench", "team"]:
						continue
					nameLink = row.find("a").get("href").split("/")
					fullName = nameLink[-1].replace("-", " ")
					playerId = int(nameLink[-2])
					playerIds[team][fullName] = playerId
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
						if td.text.lower().startswith("dnp-"):
							playerStats["min"] = 0
							break
						header = headers[tdIdx]
						if header in ["fg", "3pt", "ft"]:
							made, att = map(int, td.text.strip().split("-"))
							playerStats[header+"a"] = att
							playerStats[header+"m"] = made
						else:
							val = int(td.text.strip())
							playerStats[header] = val

					allStats[team][player] = playerStats

	for team in allStats:
		if not os.path.isdir(f"{prefix}static/basketballreference/{team}"):
			os.mkdir(f"{prefix}static/basketballreference/{team}")
		with open(f"{prefix}static/basketballreference/{team}/{date}.json", "w") as fh:
			json.dump(allStats[team], fh, indent=4)

	write_totals()

	with open(f"{prefix}static/basketballreference/playerIds.json", "w") as fh:
		json.dump(playerIds, fh, indent=4)

def write_totals():
	totals = {}
	for team in os.listdir(f"{prefix}static/basketballreference/"):
		if team not in totals:
			totals[team] = {}

		for file in glob(f"{prefix}static/basketballreference/{team}/*.json"):
			with open(file) as fh:
				stats = json.load(fh)
			for player in stats:
				if player not in totals[team]:
					totals[team][player] = stats[player]
				else:
					for header in stats[player]:
						if header not in totals[team][player]:
							totals[team][player][header] = 0
						totals[team][player][header] += stats[player][header]

				if "gamesPlayed" not in totals[team][player]:
					totals[team][player]["gamesPlayed"] = 0
				if stats[player]["min"] > 0:
					totals[team][player]["gamesPlayed"] += 1

	with open(f"{prefix}static/basketballreference/totals.json", "w") as fh:
		json.dump(totals, fh, indent=4)

def write_averages():
	with open(f"{prefix}static/basketballreference/playerIds.json") as fh:
		ids = json.load(fh)

	with open(f"{prefix}static/basketballreference/averages.json") as fh:
		averages = json.load(fh)

	lastYearStats = {}
	headers = ["min", "fg", "fg%", "3pt", "3p%", "ft", "ft%", "reb", "ast", "blk", "stl", "pf", "to", "pts"]
	for team in ids:
		if team not in averages:
			averages[team] = {}
		if team not in lastYearStats:
			lastYearStats[team] = {}

		for player in ids[team]:
			pId = ids[team][player]
			if player in averages[team]:
				pass
				continue
			
			gamesPlayed = 0
			averages[team][player] = {}
			lastYearStats[team][player] = {}

			time.sleep(0.175)
			url = f"https://www.espn.com/nba/player/gamelog/_/id/{pId}/type/nba/year/2022"
			outfile = "out"
			call(["curl", "-k", url, "-o", outfile])
			soup = BS(open(outfile, 'rb').read(), "lxml")

			for row in soup.findAll("tr"):
				if row.text.startswith("Averages"):
					for idx, td in enumerate(row.findAll("td")[1:]):
						header = headers[idx]
						if header in ["fg", "3pt", "ft"]:
							made, att = map(float, td.text.strip().split("-"))
							averages[team][player][header+"a"] = att
							averages[team][player][header+"m"] = made
						else:
							val = float(td.text.strip())
							averages[team][player][header] = val
					averages[team][player]["gamesPlayed"] = gamesPlayed
				else:
					tds = row.findAll("td")
					if len(tds) > 1 and ("@" in tds[1].text or "vs" in tds[1].text):
						date = str(datetime.datetime.strptime(tds[0].text.strip(), "%a %m/%d")).split(" ")[0][6:]
						lastYearStats[team][player][date] = {}
						for idx, td in enumerate(tds[3:]):
							header = headers[idx]
							if header == "min" and int(td.text.strip()) > 0:
								gamesPlayed += 1

							if header in ["fg", "3pt", "ft"]:
								made, att = map(int, td.text.strip().split("-"))
								lastYearStats[team][player][date][header+"a"] = att
								lastYearStats[team][player][date][header+"m"] = made
							else:
								val = float(td.text.strip())
								lastYearStats[team][player][date][header] = val

	with open(f"{prefix}static/basketballreference/averages.json", "w") as fh:
		json.dump(averages, fh, indent=4)

	with open(f"{prefix}static/basketballreference/lastYearStats.json", "w") as fh:
		json.dump(lastYearStats, fh, indent=4)


def write_schedule(date):
	url = f"https://www.espn.com/nba/schedule/_/date/{date.replace('-','')}"
	outfile = "out"
	call(["curl", "-k", url, "-o", outfile])
	soup = BS(open(outfile, 'rb').read(), "lxml")

	with open(f"{prefix}static/basketballreference/boxscores.json") as fh:
		boxscores = json.load(fh)

	with open(f"{prefix}static/basketballreference/schedule.json") as fh:
		schedule = json.load(fh)

	for table in soup.findAll("div", class_="ResponsiveTable"):
		date = table.find("div", class_="Table__Title").text.strip()
		date = str(datetime.datetime.strptime(date, "%A, %B %d, %Y"))[:10]
		if date not in boxscores:
			boxscores[date] = {}
		if date not in schedule:
			schedule[date] = []

		for row in table.findAll("tr")[1:]:
			tds = row.findAll("td")
			awayTeam = tds[0].findAll("a")[-1].get("href").split("/")[-2]
			homeTeam = tds[1].findAll("a")[-1].get("href").split("/")[-2]
			boxscore = tds[2].find("a").get("href")
			boxscores[date][f"{awayTeam} @ {homeTeam}"] = boxscore
			schedule[date].append(f"{awayTeam} @ {homeTeam}")

	with open(f"{prefix}static/basketballreference/boxscores.json", "w") as fh:
		json.dump(boxscores, fh, indent=4)

	with open(f"{prefix}static/basketballreference/schedule.json", "w") as fh:
		json.dump(schedule, fh, indent=4)

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("-c", "--cron", action="store_true", help="Start Cron Job")
	parser.add_argument("-d", "--date", help="Date")
	parser.add_argument("-s", "--start", help="Start Week", type=int)
	parser.add_argument("-e", "--end", help="End Week", type=int)
	parser.add_argument("-w", "--week", help="Week", type=int)

	args = parser.parse_args()

	if args.start:
		curr_week = args.start

	date = args.date
	if not date:
		date = datetime.datetime.now()
		date = str(date)[:10]

	if args.cron:
		pass
		#write_schedule(date)
		write_stats(date)
		#write_averages()
		
