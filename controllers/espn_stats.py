
from bs4 import BeautifulSoup

import argparse
import os
import sys
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
	if name == "paul richardson":
		return "paul richardson jr."
	elif name == "allen robinson":
		return "allen robinson ii"
	return name

def write_cron_espn_stats(curr_week, end_week):
	espn_stats = {}
	for week in range(curr_week,end_week):
		for idx in range(0,1001,20):

			html = urllib.urlopen("http://games.espn.com/ffl/tools/projections?&scoringPeriodId={}&seasonId=2018&startIndex={}".format(week,idx)).read()
			soup = BeautifulSoup(html, "lxml")
			player_rows = soup.find_all("tr", class_="pncPlayerRow")

			for row in player_rows:
				all_tds = row.find_all("td")
				name_link = all_tds[0].find("a")
				full_name_arr = name_link.text.split(" ")
				team_div = name_link.next_sibling
				team_div = re.sub(r'[^\x00-\x7f]',r' ', team_div)
				team = team_div.split(" ")[1]
				space = " "
				full_name = fix_name(name_link.text.lower().replace("'", ""))
				#full_name = full_name_arr[0][0] + '. ' + space.join(full_name_arr[1:])
				try:
					rec = float(all_tds[-4].text)
					proj = float(all_tds[-1].text)
				
					proj -= (rec / 2.0)
					proj = "%.2f" % round(proj, 2)

					if full_name not in espn_stats:
						espn_stats[full_name] = float(proj)
					"""
					pid = getPlayerID(full_name,team)

					if pid == None:
						createPlayer(pid, full_name, team)
					else:
						pid = pid[0]
						proj = "%.2f" % round(proj, 2)
						updateESPNStats(pid, week, proj)
					"""
				except:
					pass
		
		if os.path.isdir("static/projections/{}".format(week)) is False:
			os.mkdir("static/projections/{}".format(week))
		with open("static/projections/{}/espn.json".format(week), "w") as outfile:
			json.dump(espn_stats, outfile, indent=4)
	
	
def write_cron_espn_rankings(curr_week, end_week):
	print("WRITING ACTUAL RANKINGS")
	espn_actual = {}
	for idx, position in enumerate(["qb", "rb", "wr", "te"]):
		espn_actual[position] = []
		
		for start_idx in range(0, 100, 50):
			url = "http://games.espn.com/ffl/leaders?&scoringPeriodId={}&slotCategoryId={}&startIndex={}".format(curr_week, idx * 2, start_idx)
			html = urllib.urlopen(url).read()
			soup = BeautifulSoup(html, "lxml")
			player_rows = soup.find_all("tr", class_="pncPlayerRow")

			for row in player_rows:
				all_tds = row.find_all("td")
				name_link = all_tds[0].find("a")
				full_name_arr = name_link.text.split(" ")
				full_name = fix_name(name_link.text.lower().replace("'", ""))
				try:
					rec = float(all_tds[-8].text)
					act = float(all_tds[-1].text)
					
					if position != "qb":
						act -= (rec / 2.0)

					if full_name not in espn_actual[position]:
						espn_actual[position].append({"actual": round(act, 2), "name": full_name})
				except:
					pass
		espn_ranks = {}
		espn_actual_sorted = sorted(espn_actual[position], key=operator.itemgetter("actual"), reverse=True)
		for rank_idx, rank in enumerate(espn_actual_sorted):
			espn_ranks[rank["name"]] = rank_idx + 1

		if os.path.isdir("static/rankings/{}".format(curr_week)) is False:
			os.mkdir("static/rankings/{}".format(curr_week))

		if os.path.isdir("static/rankings/{}/{}".format(curr_week, position)) is False:
			os.mkdir("static/rankings/{}/{}".format(curr_week, position))

		with open("static/rankings/{}/{}/rankings.json".format(curr_week, position), "w") as fh:
			json.dump(espn_ranks, fh, indent=4)


def read_actual_rankings(curr_week, end_week):
	espn_json = {}
	for position in ["qb", "rb", "wr", "te"]:
		espn_json[position] = {}
		with open("static/rankings/{}/{}/rankings.json".format(curr_week, position)) as fh:
			espn_json[position] = json.loads(fh.read())
	return espn_json

def read_espn_stats(curr_week, end_week):
	espn_json = {}
	for week in range(curr_week, end_week):
		with open("static/projections/{}/espn.json".format(week)) as fh:
			returned_json = json.loads(fh.read())
			espn_json = merge_two_dicts(returned_json, espn_json)
	return espn_json

def read_espn_rankings(curr_week, players_on_teams):
	espn_json = read_espn_stats(curr_week, curr_week + 1)
	espn_list = {"qb": [], "rb": [], "wr": [], "te": []}
	for player in espn_json:

		if player in players_on_teams:
			position = players_on_teams[player]["position"].lower()
			if position in ["qb", "rb", "wr", "te"]:
				espn_list[position].append({"name": player, "proj": espn_json[player]})

	espn_json = {}
	for position in ["qb", "rb", "wr", "te"]:
		espn_list[position] = sorted(espn_list[position], key=operator.itemgetter("proj"), reverse=True)
		espn_json[position] = {}
		for idx, player_json in enumerate(espn_list[position]):
			espn_json[position][player_json["name"]] = idx + 1
	return espn_json


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
		print("WRITING ESPN STATS")
		write_cron_espn_stats(curr_week, end_week)
		write_cron_espn_rankings(curr_week, end_week)
	else:
		read_espn_stats(curr_week, end_week)

