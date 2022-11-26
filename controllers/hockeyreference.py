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
	with open(f"{prefix}static/hockeyreference/boxscores.json") as fh:
		boxscores = json.load(fh)

	with open(f"{prefix}static/hockeyreference/playerIds.json") as fh:
		playerIds = json.load(fh)

	dates = [date]
	#dates = ["2022-10-11", "2022-10-12", "2022-10-13", "2022-10-14", "2022-10-15", "2022-10-17", "2022-10-18", "2022-10-19", "2022-10-20", "2022-10-21", "2022-10-22", "2022-10-23"]
	for date in dates:

		if date not in boxscores:
			print("No games found for this date, grabbing schedule")
			write_schedule(date)
			with open(f"{prefix}static/hockeyreference/boxscores.json") as fh:
				boxscores = json.load(fh)

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

			chkPre = soup.find("div", class_="ScoreCell__NotesWrapper")
			if chkPre and chkPre.text.strip().lower() == "preseason":
				continue

			# tables are split with players then stats, players -> stats
			headers = []
			playerList = []
			team = away
			for idx, table in enumerate(soup.findAll("table")[1:9]):
				if idx in [2,4,6]:
					playerList = []
				if idx == 4:
					team = home

				if team not in playerIds:
					playerIds[team] = {}

				playerIdx = 0
				for row in table.findAll("tr"):
					if idx in [0,2,4,6]:
						# PLAYERS
						if row.text.strip().lower() in ["skaters", "defensemen", "goalies"]:
							continue
						if not row.find("a"):
							continue
						nameLink = row.find("a").get("href").split("/")
						fullName = row.find("a").text.lower().title().replace("-", " ")
						if fullName.startswith("J.T."):
							fullName = fullName.replace("J.T.", "J.")
						elif fullName.startswith("J.J."):
							fullName = fullName.replace("J.J.", "J.")
						elif fullName.startswith("T.J."):
							fullName = fullName.replace("T.J.", "T.")
						elif fullName.startswith("A.J."):
							fullName = fullName.replace("A.J.", "A.")
						playerId = int(nameLink[-1])
						playerIds[team][fullName] = playerId
						playerList.append(fullName)
					else:
						# idx==1 or 3. STATS
						if not row.find("td"):
							continue
						firstTd = row.find("td").text.strip().lower()
						if firstTd in ["g", "sa"]:
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
							header = headers[tdIdx]
							val = 0
							if header in ["toi", "pptoi", "shtoi", "estoi"]:
								valSp = td.text.strip().split(":")
								val = int(valSp[0])+round(int(valSp[1]) / 60, 2)
							else:
								val = float(td.text.strip())
							playerStats[header] = val

						allStats[team][player] = playerStats

		for team in allStats:
			if not os.path.isdir(f"{prefix}static/hockeyreference/{team}"):
				os.mkdir(f"{prefix}static/hockeyreference/{team}")
			with open(f"{prefix}static/hockeyreference/{team}/{date}.json", "w") as fh:
				json.dump(allStats[team], fh, indent=4)

	write_totals()

	with open(f"{prefix}static/hockeyreference/playerIds.json", "w") as fh:
		json.dump(playerIds, fh, indent=4)

def write_totals():
	totals = {}
	for team in os.listdir(f"{prefix}static/hockeyreference/"):
		if team not in totals:
			totals[team] = {}

		for file in glob(f"{prefix}static/hockeyreference/{team}/*.json"):
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
				#print(team,player)
				if float(stats[player]["toi"]) > 0:
					totals[team][player]["gamesPlayed"] += 1

	with open(f"{prefix}static/hockeyreference/totals.json", "w") as fh:
		json.dump(totals, fh, indent=4)

def write_averages():
	with open(f"{prefix}static/hockeyreference/playerIds.json") as fh:
		ids = json.load(fh)

	with open(f"{prefix}static/hockeyreference/averages.json") as fh:
		averages = json.load(fh)

	with open(f"{prefix}static/hockeyreference/lastYearStats.json") as fh:
		lastYearStats = json.load(fh)

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
			url = f"https://www.espn.com/nhl/player/gamelog/_/id/{pId}/type/nhl/year/2022"
			outfile = "out"
			call(["curl", "-k", url, "-o", outfile])
			soup = BS(open(outfile, 'rb').read(), "lxml")

			headers = []
			for row in soup.findAll("tr"):
				if not headers and row.text.lower().startswith("date"):
					tds = row.findAll("td")[3:]
					if not tds:
						tds = row.findAll("th")[3:]
					for td in tds:
						headers.append(td.text.strip().lower())
				elif row.text.startswith("Totals"):
					for idx, td in enumerate(row.findAll("td")[1:]):
						header = headers[idx]
						if header in ["toi/g", "prod"]:
							valSp = td.text.strip().split(":")
							val = int(valSp[0])+round(int(valSp[1]) / 60, 2)
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
							if header == "toi/g" and float(td.text.strip().replace(":", ".")) > 0:
								gamesPlayed += 1

							val = 0.0
							if header in ["toi/g", "prod"]:
								valSp = td.text.strip().split(":")
								if len(valSp) > 1:
									val = int(valSp[0])+round(int(valSp[1]) / 60, 2)
							else:
								val = float(td.text.strip())
							lastYearStats[team][player][date][header] = val

	with open(f"{prefix}static/hockeyreference/averages.json", "w") as fh:
		json.dump(averages, fh, indent=4)

	if lastYearStats:
		with open(f"{prefix}static/hockeyreference/lastYearStats.json", "w") as fh:
			json.dump(lastYearStats, fh, indent=4)


def write_schedule(date):
	url = f"https://www.espn.com/nhl/schedule/_/date/{date.replace('-', '')}"
	outfile = "out"
	call(["curl", "-k", url, "-o", outfile])
	soup = BS(open(outfile, 'rb').read(), "lxml")

	with open(f"{prefix}static/hockeyreference/schedule.json") as fh:
		schedule = json.load(fh)

	with open(f"{prefix}static/hockeyreference/boxscores.json") as fh:
		boxscores = json.load(fh)

	schedule[date] = []

	for table in soup.findAll("div", class_="ResponsiveTable"):
		if not table.find("div", class_="Table__Title"):
			continue
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

	with open(f"{prefix}static/hockeyreference/boxscores.json", "w") as fh:
		json.dump(boxscores, fh, indent=4)

	with open(f"{prefix}static/hockeyreference/schedule.json", "w") as fh:
		json.dump(schedule, fh, indent=4)

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("-c", "--cron", action="store_true", help="Start Cron Job")
	parser.add_argument("-d", "--date", help="Date")
	parser.add_argument("-s", "--start", help="Start Week", type=int)
	parser.add_argument("--schedule", help="Schedule", action="store_true")
	parser.add_argument("-e", "--end", help="End Week", type=int)
	parser.add_argument("-w", "--week", help="Week", type=int)

	args = parser.parse_args()

	if args.start:
		curr_week = args.start

	date = args.date
	if not date:
		date = datetime.datetime.now()
		date = str(date)[:10]

	if args.schedule:
		write_schedule(date)
	elif args.cron:
		pass
		write_schedule(date)
		write_stats(date)
		#write_totals()
		#write_averages()
