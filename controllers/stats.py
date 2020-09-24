
from bs4 import BeautifulSoup as BS

import argparse
import json
import os
import re

def team_trans(team):
	if team == "WSH":
		return "WAS"
	return team

def parse_data(data):
	out = ""
	points = 0
	#### QB
	if "Passing_YDS" in data:
		out += f" Passing: {data['Passing_C/ATT']} {data['Passing_YDS']} Yards"
		points += 0.04 * data["Passing_YDS"]
		if "Passing_TD" in data and data["Passing_TD"]:
			out += f", {data['Passing_TD']} TD"
			points += 4 * data["Passing_TD"]
		if "Passing_INT" in data and data["Passing_INT"]:
			out += f", {data['Passing_INT']} INT"
			points += -2 * data["Passing_INT"]
	#### RB
	if "Rushing_YDS" in data and data["Rushing_YDS"]:
		out += f" Rushing: {data['Rushing_CAR']} Car {data['Rushing_YDS']} Yards"
		points += 0.10 * data["Rushing_YDS"]
		if "Rushing_TD" in data and data["Rushing_TD"]:
			out += f", {data['Rushing_TD']} TD"
			points += 6 * data["Rushing_TD"]
	#### WR
	if "Receiving_REC" in data and data["Receiving_REC"]:
		out += f" Receiving: {data['Receiving_REC']} Rec / {data['Receiving_TGTS']} Tgt {data['Receiving_YDS']} Yards"
		points += 0.5 * data["Receiving_REC"]
		points += 0.10 * data["Receiving_YDS"]
		if "Receiving_TD" in data and data["Receiving_TD"]:
			out += f", {data['Receiving_TD']} TD"
			points += 6 * data["Receiving_TD"]
	#### Fumbles
	if "Fumbles_LOST" in data and data["Fumbles_LOST"]:
		out += f", {data['Fumbles_LOST']} Fumbles"
		points += -2 * data["Fumbles_LOST"]
	return out, round(points, 2)

def parse_fantasy_points(all_stats):
	stats = {}
	for player in all_stats:
		data = all_stats[player]
		out, points = parse_data(data)
		stats[player] = {"statline": out, "points": points}
	return stats


def get_boxscores(week):
	base_url = "https://www.espn.com/nfl/scoreboard/_/year/2020/seasontype/2/week"
	all_stats = {}
	if not os.path.exists(f"static/stats/{week}/espn_scoreboards.html"):
		os.system(f"curl -k \"{base_url}/{week}\" -o static/stats/{week}/espn_scoreboards.html")
	with open(f"static/stats/{week}/espn_scoreboards.html") as fh:
		lines = [line for line in fh.readlines() if line.strip()]
	data = ""
	for idx, line in enumerate(lines):
		m = re.search(r"window\.espn\.scoreboardData\s+=? (.*?)};", line)
		if m:
			data = m.group(1).replace("false", "False").replace("true", "True") + "}"
			break
	data = eval(data)
	links = []
	for row in data["events"]:
		links.append(row["links"][1]["href"])
	return links

def parse_boxscores(week, links):
	stats = {}
	for link in links:
		link = link.replace("http:", "https:")
		gameid = link.split("=")[-1]
		if not os.path.exists(f"static/stats/{week}/espn_{gameid}.html"):
			os.system(f"curl -k \"{link}\" -o static/stats/{week}/espn_{gameid}.html")
		with open(f"static/stats/{week}/espn_{gameid}.html") as fh:
			soup = BS(fh.read(), "lxml")
		for table in soup.find("article").find_all("table"):
			team_name = table.findPrevious("div", class_="team-name")
			team = team_name.find("img").get("src").split("/")[-1].split(".")[0].upper()
			team = team_trans(team)
			which = team_name.text.split(" ")[-1]

			if which == "Defensive":
				break
			headers = []
			for col in table.find_all("tr")[0].find_all("th"):
				headers.append(col.text)
			for row in table.find_all("tr")[1:]:
				try:
					player = row.find("td").find("span").text
					player += f" {team}"
					abbr = row.find("td").find_all("span")[-1].text
				except:
					continue
				if player not in stats:
					stats[player] = {"team": team, "abbr": abbr}
				for idx, col in enumerate(row.find_all("td")[1:]):
					if "/" in col.text or ("-" in col.text and not col.text.startswith("-")):
						stats[player][which+"_"+headers[idx+1]] = col.text
					elif "." in col.text:
						stats[player][which+"_"+headers[idx+1]] = float(col.text)
					elif col.text != "--":
						stats[player][which+"_"+headers[idx+1]] = int(col.text)
	fantasy_points = parse_fantasy_points(stats)
	with open(f"static/stats/{week}/fantasy.json", "w") as fh:
		json.dump(fantasy_points, fh, indent=4)

def write_stats(start, end):
	for week in range(start, end):
		if not os.path.exists(f"static/stats/{week}"):
			os.mkdir(f"static/stats/{week}")
		links = get_boxscores(week)
		stats = parse_boxscores(week, links)

def write_ff_stats(start, end):
	base_url = "https://www.fftoday.com/stats/playerstats.php?Season=2020&GameWeek=2&PosID=10"
	all_stats = {}
	for week in range(start, end):
		if not os.path.exists(f"static/stats/{week}"):
			os.mkdir(f"static/stats/{week}")
		for pos, pos_id in POSITIONS:
			if pos not in all_stats:
				all_stats[pos] = {}
			stats_cutoff = 3
			if pos == "DEF":
				stats_cutoff = 2
			url = f"{base_url}&GameWeek={week}&PosID={pos_id}"
			if not os.path.exists(f"static/stats/{week}/{pos}.html"):
				os.system(f"curl -k \"{url}\" -o static/stats/{week}/{pos}.html")
			with open(f"static/stats/{week}/{pos}.html") as fh:
				soup = BS(fh.read(), "lxml")
			# get if passing/rushing since TD is shared below
			top_headers = []
			for col in soup.find_all("table")[-2].find_all("tr")[0].find_all("td")[1:]:
				for i in range(int(col.get("colspan"))):
					top_headers.append(col.text)
			headers = []
			for idx, row in enumerate(soup.find_all("table")[-2].find_all("tr")[1].find_all("td")[stats_cutoff:]):
				prefix = top_headers[idx]
				headers.append(prefix+"_"+row.find("b").text)
			for row in soup.find_all("table")[-2].find_all("tr")[2:]:
				cols = row.find_all("td")
				player = cols[0].find("a").text
				team = cols[1].text
				stats = {}
				for idx, col in enumerate(cols[stats_cutoff:]):
					if "%" in col.text:
						stats[headers[idx]] = col.text
					elif "." in col.text:
						stats[headers[idx]] = float(col.text)
					else:
						stats[headers[idx]] = int(col.text)
				all_stats[pos][player] = stats
	fantasy_points = parse_fantasy_points(all_stats)

if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument("-c", "--cron", help="Do Cron job", action="store_true")
	parser.add_argument("-s", "--start", help="Start Week", type=int, default=1)
	parser.add_argument("-e", "--end", help="End Week", type=int)
	args = parser.parse_args()

	start = 1
	end = 2
	if args.start:
		start = args.start
	if args.end:
		end = args.end
	else:
		end = start + 1

	if args.cron:
		write_stats(start, end)