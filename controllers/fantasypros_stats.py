
from bs4 import BeautifulSoup

import argparse
import sys
import os
import re
import operator
import json
from lxml import etree
try:
	import urllib2 as urllib
except:
	import urllib.request as urllib


def merge_two_dicts(x, y):
	z = x.copy()
	z.update(y)
	return z

def fix_name(name):
	if name == "todd gurley":
		return "todd gurley ii"
	elif name == "mitch trubisky":
		return "mitchell trubisky"
	elif name == "willie snead":
		return "willie snead iv"
	elif name == "allen robinson":
		return "allen robinson ii"
	elif name == "ted ginn":
		return "ted ginn jr."
	elif name == "marvin jones":
		return "marvin jones jr."
	elif name == "will fuller":
		return "will fuller v"
	elif name == "paul richardson":
		return "paul richardson jr."
	return name

def write_cron_fantasypros_rankings(curr_week=1):
	fantasypros_stats = {}
	for position in ["qb", "rb", "wr", "te"]:
		fantasypros_stats = {}
		path = "half-point-ppr-{}".format(position) if position != "qb" else "qb"
		url = "https://www.fantasypros.com/nfl/rankings/{}.php?scoring=HALF&week={}".format(path, curr_week)
		html = urllib.urlopen(url, "lxml")
		soup = BeautifulSoup(html, "lxml")
		player_rows = soup.find("table", id="rank-data").find("tbody").find_all("tr")

		for row in player_rows:
			if row.find("span", class_="full-name") is None:
				continue
			name = row.find("span", class_="full-name").text
			full_name = fix_name(name.lower().replace("'", ""))
			rank = int(row.find_all("td")[0].text)

			if full_name not in fantasypros_stats:
				fantasypros_stats[full_name] = rank

		if os.path.isdir("static/rankings/{}/{}".format(curr_week, position)) is False:
			os.mkdir("static/rankings/{}/{}".format(curr_week, position))
		with open("static/rankings/{}/{}/fantasypros.json".format(curr_week, position), "w") as outfile:
			json.dump(fantasypros_stats, outfile, indent=4)


def write_cron_fantasypros_stats(curr_week=1):
	
	fantasypros_stats = {}
	for position in ["qb", "rb", "wr", "te"]:

		url = "https://www.fantasypros.com/nfl/projections/{}.php?scoring=HALF&week={}".format(position, curr_week)
		html = urllib.urlopen(url, "lxml")
		soup = BeautifulSoup(html, "lxml")
		player_rows = soup.find("table", id="data").find("tbody").find_all("tr")

		for row in player_rows:
			name = row.find("a", class_="player-name").text
			full_name = fix_name(name.lower().replace("'", ""))
			proj = float(row.find_all("td")[-1].text)
			
			if full_name not in fantasypros_stats:
				fantasypros_stats[full_name] = proj

	with open("static/projections/{}/fantasypros.json".format(curr_week), "w") as outfile:
		json.dump(fantasypros_stats, outfile, indent=4)

def read_fantasypros_stats(curr_week, end_week):
	fantasypros_json = {}
	with open("static/projections/{}/fantasypros.json".format(curr_week)) as fh:
		fantasypros_json = json.loads(fh.read())
	return fantasypros_json

def read_fantasypros_rankings(curr_week, end_week):
	fantasypros_json = {}
	for position in ["qb", "rb", "wr", "te"]:
		fantasypros_json[position] = {}
		with open("static/rankings/{}/{}/fantasypros.json".format(curr_week, position)) as fh:
			fantasypros_json[position] = json.loads(fh.read())
	return fantasypros_json

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("-c", "--cron", help="Do Cron job", action="store_true")
	parser.add_argument("-s", "--start", help="Start Week", type=int)
	parser.add_argument("-e", "--end", help="End Week", type=int)

	args = parser.parse_args()

	curr_week = 1
	end_week = 2

	if args.start:
		curr_week = args.start
		end_week = curr_week + 1
		if args.end:
			end_week = args.end
	
	if args.cron:
		print("WRITING FANTASYPROS STATS")
		write_cron_fantasypros_stats(curr_week)
		write_cron_fantasypros_rankings(curr_week)
	else:
		read_fantasypros_stats(curr_week, end_week)