from bs4 import BeautifulSoup
from pprint import pprint
import argparse
import os
import json

try:
	from controllers.functions import *
	from controllers.profootballreference import *
	from controllers.read_rosters import *
	from controllers.reddit import *
	from controllers.snap_stats import *
except:
	from functions import *
	from profootballreference import *
	from read_rosters import *
	from snap_stats import *
	from reddit import *
try:
	import urllib2 as urllib
except:
	import urllib.request as urllib

prefix = ""
if os.path.exists("/home/zhecht/fantasy"):
    # if on linux aka prod
    prefix = "/home/zhecht/fantasy/"

full_team_names = {
	"lar": "Rams",
	"no": "Saints",
	"phi": "Eagles",
	"lv": "Raiders",
	"ind": "Colts",
	"bal": "Ravens",
	"ne": "Patriots",
	"hou": "Texans",
	"sf": "49ers",
	"lac": "Chargers",
	"cin": "Bengals",
	"kc": "Chiefs",
	"atl": "Falcons",
	"pit": "Steelers",
	"den": "Broncos",
	"jax": "Jaguars",
	"det": "Lions",
	"chi": "Bears",
	"gb": "Packers",
	"nyj": "Jets",
	"nyg": "Giants",
	"ten": "Titans",
	"dal": "Cowboys",
	"min": "Vikings",
	"was": "Washington",
	"tb": "Buccaneers",
	"cle": "Browns",
	"sea": "Seahawks",
	"car": "Panthers",
	"ari": "Cardinals",
	"mia": "Dolphins",
	"buf": "Bills"
}

def merge_two_dicts(x, y):
	z = x.copy()
	z.update(y)
	return z

def read_nfl_trades():
	with open(f"{prefix}static/nfl_trades.json") as fh:
		returned_json = json.loads(fh.read())
	return returned_json

def write_redzone(curr_week=1):
	redzone_json = {}
	team_total_json = {}
	nfl_trades = read_nfl_trades()

	for team in SNAP_LINKS:
		link = f"http://www.footballguys.com/stats/redzone/teams?team={team.upper()}&year={YEAR}"
		opps = get_opponents(TEAM_TRANS.get(team, team))
		html = urllib.urlopen(link)
		soup = BeautifulSoup(html.read(), "lxml")

		team_total_json[team] = {"RB": [], "WR/TE": []}
		team_total_json[team]["RB"] = [0]*17
		team_total_json[team]["WR/TE"] = [0]*17

		# SKIP QB
		currPos = 0
		positions = ["QB", "RB", "WR", "TE"]
		rows = soup.find("div", id="stats_redzone_team_data").findAll("tr")[1:]
		for idx, row in enumerate(rows):
			tds = row.find_all('td')[:-1]
			redzone_counts = []

			if tds[0].text.strip().lower().endswith("totals"):
				currPos += 1
				continue

			full = tds[0].find('a').text
			full_name = fixName(full.lower().replace("'", ""))

			for week in range(1,curr_week+1):
				perc = 0
				if opps[week-1] != "BYE":
					try:
						perc = int(tds[week].text)
					except:
						pass

				redzone_counts.append(perc)
				pos = positions[currPos]
				if pos == "WR" or pos == "TE":
					pos = "WR/TE"

				if pos != "QB":
					team_total_json[team][pos][week - 1] += perc
				

			if full_name and pos != "QB":
				redzone_json[full_name] = {"looks": ','.join(str(x) for x in redzone_counts), "team": team, "looks_perc": ""}
	
	for player in redzone_json:
		perc_arr = []
		for week in range(curr_week):
			team = redzone_json[player]["team"]
			opps = get_opponents(team)
			looks = [int(x) for x in redzone_json[player]["looks"].split(",")]
			team_total_rb = team_total_json[team]["RB"][week]
			team_total_wrte = team_total_json[team]["WR/TE"][week]
			perc = 0 if team_total_rb + team_total_wrte == 0 else (looks[week] / float(team_total_rb + team_total_wrte))
			if opps[week] == "BYE":
				perc = 0

			perc_arr.append(round(perc, 2))

		redzone_json[player]["looks_perc"] = ','.join(str(x) for x in perc_arr)

	with open(f"{prefix}static/looks/redzone.json", "w") as outfile:
		json.dump(redzone_json, outfile, indent=4)
	with open(f"{prefix}static/looks/team_total.json", "w") as outfile:
		json.dump(team_total_json, outfile, indent=4)


def read_redzone():
	with open(f"{prefix}static/looks/redzone.json") as fh:
		returned_json = json.loads(fh.read())
	return returned_json

def read_team_total():
	with open(f"{prefix}static/looks/team_total.json") as fh:
		returned_json = json.loads(fh.read())
	return returned_json

# Adds up total redzone looks and then last weeks too
def get_redzone_totals(curr_week, trends, snap_stats, team_total_json, pos="RB"):
	redzone_totals = {}
	for team in trends:
		redzone_totals[team] = {"total": 0, "last_total": 0}
		# only count up to curr_week NOT +1
		for week in range(1, curr_week):
			redzone_totals[team]["last_total"] += team_total_json[team][pos][week - 1]
		redzone_totals[team]["total"] = redzone_totals[team]["last_total"]
		redzone_totals[team]["total"] += team_total_json[team][pos][curr_week - 1]
		for player in trends[team]:
			redzone_totals[player] = {"total": 0, "last_total": 0}
			for week in range(1, curr_week):
				redzone_totals[player]["last_total"] += int(trends[team][player]["looks"].split(",")[week - 1])
			redzone_totals[player]["total"] = redzone_totals[player]["last_total"]
			redzone_totals[player]["total"] += int(trends[team][player]["looks"].split(",")[curr_week - 1])
	#print(redzone_totals[])
	return redzone_totals

def get_target_share_totals(curr_week, target_stats):
	target_totals = {}

def subtract_missed_rz(curr_week, snap_stats, team_total):
	tot = 0
	for week in range(curr_week):
		if int(snap_stats[week]) == 0:
			tot += team_total[week]
	return tot

def getTeamNameFromYahooNFL(team):
	return team

def get_redzone_trends(rbbc_teams, curr_week=1, requested_pos="RB", is_ui=False):
	redzone_json = read_redzone()
	team_total_json = read_team_total()
	players_on_teams,translations = read_rosters()
	players_on_FA = read_FA()
	snap_stats = read_snap_stats(curr_week)
	target_stats = read_target_stats()

	players_on_teams = merge_two_dicts(players_on_teams, players_on_FA)
	update_players_on_teams(players_on_teams)
	trends = {}
	for player in snap_stats:
		#if player not in redzone_json:
		#	continue
		if player not in players_on_teams or players_on_teams[player]["position"] == "QB":
			continue

		pos = players_on_teams[player]["position"]
		team = getTeamNameFromYahooNFL(players_on_teams[player]["nfl_team"].lower())
		#team = redzone_json[player]["team"]

		if pos in requested_pos.split("/") and (len(rbbc_teams) == 0 or team in rbbc_teams):
			if team not in trends:
				trends[team] = {}
			if player not in trends[team]:
				total_looks = 0 if player not in redzone_json else sum(map(int, redzone_json[player]["looks"].split(",")))
				total_targets = 0 if player not in target_stats else sum(map(int, target_stats[player]["counts"].split(",")))
				trends[team][player] = {
					"snaps": snap_stats[player]["perc"],
					"looks": redzone_json[player]["looks"] if player in redzone_json else ",".join((['0']*curr_week)),
					"targets": target_stats[player]["counts"] if player in target_stats else ",".join((['0']*curr_week)),
					"total_targets": total_targets,
					"total_looks": total_looks
				}
	
	redzone_totals = get_redzone_totals(curr_week, trends, snap_stats, team_total_json, requested_pos)
	target_aggregates = get_target_aggregate_stats(curr_week)

	for team in trends:
		total_looks = team_total_json[team][requested_pos][curr_week - 1]

		for player in trends[team]:
			looks_arr = trends[team][player]["looks"].split(",")
			targets_arr = trends[team][player]["targets"].split(",")
			looks_per_game, last_looks_per_game, last_3_looks_per_game = get_looks_per_game(player, team, curr_week, looks_arr, snap_stats)
			targets_per_game, last_targets_per_game, last_3_targets_per_game = get_targets_per_game(player, curr_week, targets_arr, snap_stats)
			snaps_per_game, last_snaps_per_game, last_3_snaps_per_game = get_snaps_per_game(player, curr_week, snap_stats)

			rz = int(trends[team][player]["looks"].split(",")[curr_week - 1])
			last_rz = int(trends[team][player]["looks"].split(",")[curr_week - 1])
			last_snaps = float(trends[team][player]["snaps"].split(",")[curr_week - 1])
			last_2_snaps = float(trends[team][player]["snaps"].split(",")[curr_week - 2])
			#if player == "leveon bell":
			#	print(target_aggregates[player])
			target_share = 0
			if player in target_aggregates:
				target_share = round(float(target_aggregates[player]["perc"].split(",")[curr_week - 1]) * 100, 1)
			try:
				denom = redzone_totals[team]["total"] - subtract_missed_rz(curr_week, snap_stats[player]["counts"].split(","), team_total_json[team][requested_pos])
				looks_perc = round(float(redzone_totals[player]["total"] / denom) * 100, 1)
			except:
				looks_perc = 0

			if curr_week == 1:
				avg_snaps = last_snaps
				last_looks_perc = looks_perc
				last_target_share = target_share
			else:
				# last snaps get average
				avg_snaps = 0
				tot_games = 0
				for week in range(curr_week-1):
					snaps = int(trends[team][player]["snaps"].split(",")[week])
					avg_snaps += snaps
					if snaps:
						tot_games += 1
				if tot_games:
					avg_snaps = avg_snaps / tot_games

				last_looks_perc = 0
				try:
					last_looks_perc = round(float(redzone_totals[player]["last_total"] / redzone_totals[team]["last_total"]) * 100, 1)
				except:
					pass

				try:
					last_target_share = round(float(target_aggregates[player]["perc"].split(",")[curr_week - 2]) * 100, 1)
				except:
					last_target_share = 0

			snaps_trend = 0
			looks_trend = 0
			target_trend = 0
			looks_share_trend = 0
			target_share_trend = 0
			looks_per_game_trend = 0
			targets_per_game_trend = 0

			if get_opponents(team)[curr_week-1] != "BYE":
				#snaps_trend = round(snaps_per_game - avg_snaps, 1)
				looks_trend = int(trends[team][player]["looks"].split(",")[curr_week - 1])
				target_trend = int(trends[team][player]["targets"].split(",")[curr_week - 1])
				looks_share_trend = round(looks_perc - last_looks_perc, 1)
				if last_snaps == 0:
					looks_share_trend = 0
				target_share_trend = round(target_share - last_target_share, 1)
				looks_per_game_trend = round(looks_per_game - last_looks_per_game, 2)
				targets_per_game_trend = round(targets_per_game - last_targets_per_game, 2)

				snaps_per_game_trend = round(snaps_per_game - last_snaps_per_game, 2)

			trends[team][player]["looks_per_game"] = looks_per_game
			trends[team][player]["targets_per_game"] = targets_per_game
			trends[team][player]["looks_share"] = looks_perc
			trends[team][player]["snaps"] = last_snaps
			snaps_trend = last_snaps - last_2_snaps
			trends[team][player]["snapsTrend"] = str(last_snaps - last_2_snaps)+"%"
			if not trends[team][player]["snapsTrend"].startswith("-"):
				trends[team][player]["snapsTrend"] = "+"+trends[team][player]["snapsTrend"]

			trends[team][player]["avg_snaps"] = snaps_per_game
			trends[team][player]["target_share"] = target_share

			if is_ui:
				trends[team][player]["snaps_trend"] = f"+{snaps_trend}%" if snaps_trend > 0 else "{}%".format(snaps_trend or '-')
				trends[team][player]["looks_trend"] = f"+{looks_trend}" if looks_trend > 0 else "{}".format(looks_trend or '-')
				trends[team][player]["snaps_per_game_trend"] = f"+{snaps_per_game_trend}" if snaps_per_game_trend > 0 else "{}".format(snaps_per_game_trend or '-')
				trends[team][player]["targets_per_game_trend"] = f"+{targets_per_game_trend}" if targets_per_game_trend > 0 else "{}".format(targets_per_game_trend or '-')
				trends[team][player]["looks_per_game_trend"] = f"+{looks_per_game_trend}" if looks_per_game_trend > 0 else "{}".format(looks_per_game_trend or '-')
				trends[team][player]["looks_share_trend"] = f"+{looks_share_trend}%" if looks_share_trend > 0 else "{}%".format(looks_share_trend or '-')
				trends[team][player]["target_trend"] = "+{}".format(target_trend or '-') if target_trend > 0 else "{}".format(target_trend or '-')
				trends[team][player]["target_share_trend"] = f"+{target_share_trend}%" if target_share_trend > 0 else "{}%".format(target_share_trend or '-')
			else:
				trends[team][player]["snaps_trend"] = "**+{}%**".format(snaps_trend) if snaps_trend > 0 else "{}%".format(snaps_trend or '0')
				trends[team][player]["looks_trend"] = "**+{}**".format(looks_trend) if looks_trend > 0 else "{}".format(looks_trend or '-')
				trends[team][player]["snaps_per_game_trend"] = f"**+{snaps_per_game_trend}**" if snaps_per_game_trend > 0 else "{}".format(snaps_per_game_trend or '-')
				trends[team][player]["looks_per_game_trend"] = f"**+{looks_per_game_trend}**" if looks_per_game_trend > 0 else "{}".format(looks_per_game_trend or '-')
				trends[team][player]["targets_per_game_trend"] = f"**+{targets_per_game_trend}**" if targets_per_game_trend > 0 else "{}".format(targets_per_game_trend or '-')
				trends[team][player]["looks_share_trend"] = "**+{}%**".format(looks_share_trend) if looks_share_trend > 0 else "{}%".format(looks_share_trend or '0')
				trends[team][player]["target_trend"] = "**+{}**".format(target_trend) if target_trend > 0 else "{}".format(target_trend or '-')
				trends[team][player]["target_share_trend"] = "**+{}%**".format(target_share_trend) if target_share_trend > 0 else "{}%".format(target_share_trend or '0')
	return trends
	#if not is_ui:
	#	return trends
	
	new_j = {}
	for team in trends:
		players = trends[team]
		new_j[team] = {}
		for player in players:
			# without spaces
			#new_name = player.lower().replace("'", "").replace(".", "").replace(" ", "")
			#if new_name != player:
			#	new_j[team][new_name] = trends[team][player].copy()
			# no puncuation
			new_name = player.lower().replace("'", "").replace(".", "")
			if new_name != player:
				new_j[team][new_name] = trends[team][player].copy()

			if new_name.split(" ")[-1] in ["jr", "iii", "ii", "sr", "v"]:
				new_name = " ".join(new_name.split(" ")[:-1])
				new_j[team][new_name] = trends[team][player].copy()
	for team in new_j:
		for player in new_j[team]:
			trends[team][player] =  new_j[team][player].copy()

	j = {}
	for team in trends:
		for player in trends[team]:
			j[player] = trends[team][player].copy()
	return j

def get_player_looks_json(curr_week=1):
	redzone_json = read_redzone()
	team_total_json = read_team_total()
	players_on_teams,translations = read_rosters()

	top_redzone = {}
	for player in redzone_json:
		if player not in players_on_teams or players_on_teams[player]["position"] == "QB":
			continue

		looks_arr = redzone_json[player]["looks"].split(",")
		looks_perc_arr = redzone_json[player]["looks_perc"].split(",")
		total_player_looks = 0
		total_team_looks = 0
		for week in range(1, curr_week + 1):

			looks = int(looks_arr[week - 1])
			looks_perc = float(looks_perc_arr[week - 1])

			total_team_looks += team_total_json[redzone_json[player]["team"]][week - 1]
			total_player_looks += looks

		if total_team_looks != 0 and total_player_looks != 0:
			top_redzone[player] = total_player_looks
	return top_redzone

def get_looks_per_game(player, team, curr_week, looks_arr, snap_stats):
	tot_games = 0
	tot_looks = 0
	looks_per_game = 0
	last_looks_per_game = 0
	last_3_looks_per_game = 0
	for week in range(curr_week):
		if player not in snap_stats or int(snap_stats[player]["counts"].split(",")[week]) == 0:

			if week == curr_week - 4:
				last_3_looks_per_game = 0 if not tot_games else round(float(tot_looks) / tot_games, 2)
			elif week == curr_week - 2:
				last_looks_per_game = 0 if not tot_games else round(float(tot_looks) / tot_games, 2)
			continue
		tot_games += 1
		tot_looks += int(looks_arr[week])

		if week == curr_week - 4:
			last_3_looks_per_game = 0 if not tot_games else round(float(tot_looks) / tot_games, 2)
		elif week == curr_week - 2:
			last_looks_per_game = 0 if not tot_games else round(float(tot_looks) / tot_games, 2)
	if tot_games:
		looks_per_game = round(float(tot_looks) / tot_games, 2)
	return looks_per_game, last_looks_per_game, last_3_looks_per_game

def get_targets_per_game(player, curr_week, targets_arr, snap_stats):
	tot_games = 0
	tot_looks = 0
	looks_per_game = 0
	last_looks_per_game = 0
	last_3_looks_per_game = 0
	for week in range(1, curr_week+1):
		if player not in snap_stats or int(snap_stats[player]["counts"].split(",")[week-1]) == 0:
			if week == curr_week - 3:
				last_3_looks_per_game = 0 if not tot_games else round(float(tot_looks) / tot_games, 2)
			elif week == curr_week - 1:
				last_looks_per_game = 0 if not tot_games else round(float(tot_looks) / tot_games, 2)
			continue
		tot_games += 1
		tot_looks += int(targets_arr[week-1])
		if week == curr_week - 3:
			last_3_looks_per_game = 0 if not tot_games else round(float(tot_looks) / tot_games, 2)
		elif week == curr_week - 1:
			last_looks_per_game = 0 if not tot_games else round(float(tot_looks) / tot_games, 2)
	if tot_games:
		looks_per_game = round(float(tot_looks) / tot_games, 2)
	return looks_per_game, last_looks_per_game, last_3_looks_per_game

def get_snaps_per_game(player, curr_week, snap_stats):
	tot_games = 0
	tot_looks = 0
	looks_per_game = 0
	last_looks_per_game = 0
	last_3_looks_per_game = 0
	for week in range(0, curr_week):	
		if player not in snap_stats or int(snap_stats[player]["counts"].split(",")[week]) == 0:
			if week == curr_week - 3:
				last_3_looks_per_game = 0 if not tot_games else round(float(tot_looks) / tot_games, 2)
			elif week == curr_week - 1:
				last_looks_per_game = 0 if not tot_games else round(float(tot_looks) / tot_games, 2)
			continue
		tot_games += 1
		tot_looks += int(snap_stats[player]["perc"].split(",")[week])

		if week == curr_week - 3:
			last_3_looks_per_game = 0 if not tot_games else round(float(tot_looks) / tot_games, 2)
		elif week == curr_week - 1:
			last_looks_per_game = 0 if not tot_games else round(float(tot_looks) / tot_games, 2)
	if tot_games:
		looks_per_game = round(float(tot_looks) / tot_games, 2)
	return looks_per_game, last_looks_per_game, last_3_looks_per_game


def get_player_looks_arr(curr_week=1, is_ui=False):
	redzone_json = read_redzone()
	team_total_json = read_team_total()
	players_on_teams,translations = read_rosters()
	players_on_FA = read_FA()
	snap_stats = read_snap_stats(curr_week)

	players_on_teams = {**players_on_teams, **players_on_FA}
	top_redzone = []

	for player in snap_stats:
		if player not in players_on_teams or players_on_teams[player]["position"] == "QB":
			continue

		if player not in redzone_json:
			continue

		looks_arr = redzone_json[player]["looks"].split(",")
		looks_perc_arr = redzone_json[player]["looks_perc"].split(",")
		total_player_looks = 0
		total_rb_looks = 0
		total_wrte_looks = 0
		last_total_player_looks = 0
		last_total_rb_looks = 0
		last_total_wrte_looks = 0
		gamesPlayed = 0

		for week in range(1, curr_week+1):
			if player not in snap_stats or int(snap_stats[player]["counts"].split(",")[week - 1]) == 0:
				continue

			gamesPlayed += 1
			looks = int(looks_arr[week - 1])

			looks_perc = float(looks_perc_arr[week - 1])
			total_rb_looks += team_total_json[redzone_json[player]["team"]]["RB"][week - 1]
			total_wrte_looks += team_total_json[redzone_json[player]["team"]]["WR/TE"][week - 1]
			total_player_looks += looks

		looks_per_game, last_looks_per_game, last_3_looks_per_game = get_looks_per_game(player, redzone_json[player]["team"], curr_week, looks_arr, snap_stats)

		total_team_looks = total_rb_looks + total_wrte_looks

		#if redzone_json[player]["team"] == "dal":
		#	print(player, week, total_team_looks)

		last_total_team_looks = total_team_looks - team_total_json[redzone_json[player]["team"]]["RB"][curr_week - 1] - team_total_json[redzone_json[player]["team"]]["WR/TE"][curr_week - 1]
		
		last_3_total_team_looks = last_total_team_looks - team_total_json[redzone_json[player]["team"]]["RB"][curr_week - 2] - team_total_json[redzone_json[player]["team"]]["WR/TE"][curr_week - 2] - team_total_json[redzone_json[player]["team"]]["RB"][curr_week - 3] - team_total_json[redzone_json[player]["team"]]["WR/TE"][curr_week - 3]

		try:
			looks_perc = round((float(total_player_looks) / total_team_looks) * 100, 2)
			if last_total_team_looks == 0:
				last_looks_perc = 0
			elif curr_week >= 2:
				last_looks_perc = round((float(total_player_looks - int(looks_arr[curr_week - 1])) / last_total_team_looks) * 100, 2)
			else:
				last_looks_perc = looks_perc if curr_week == 1 else 0
			last_3_looks_perc = looks_perc if curr_week == 1 else 0
			if curr_week >= 4:
				if last_3_total_team_looks == 0:
					last_3_looks_perc = 0
				else:
					last_3_looks_perc = round((float(total_player_looks - int(looks_arr[curr_week - 3]) - int(looks_arr[curr_week - 2]) - int(looks_arr[curr_week - 1])) / last_3_total_team_looks) * 100, 2)
			else:
				last_3_looks_perc = looks_perc if curr_week == 1 else 0
		except:
			#print(player, total_team_looks, last_total_team_looks, last_3_total_team_looks)
			continue

		delta = round(looks_per_game - last_looks_per_game, 2)
		delta3 = round(looks_per_game - last_3_looks_per_game, 2)
		opps = get_opponents(redzone_json[player]["team"])

		if is_ui:
			if delta == 0 or opps[week-1] == "BYE":
				delta = "-"
			else:
				delta = f"+{delta}" if delta > 0 else f"{delta}"
			if delta3:
				delta3 = f"+{delta3}" if delta3 > 0 else f"{delta3}"
			else:
				delta3 = "-"
		else:
			if delta == 0 or opps[week] == "BYE":
				delta = "-"
			else:
				delta = f"**+{delta}**" if delta > 0 else f"{delta}"
			if delta3:
				delta3 = f"**+{delta3}**" if delta3 > 0 else f"{delta3}"
			else:
				delta3 = "-"

		#if int(snap_stats[player]["counts"].split(",")[curr_week - 1]) == 0:
		#	delta = 0

		#if total_team_looks != 0 and total_player_looks != 0:
		if total_team_looks != 0:
			top_redzone.append({"name": player, "gamesPlayed": gamesPlayed, "looks_per_game": looks_per_game, "looks": total_player_looks, "looks_perc": looks_perc, "total_team_looks": total_team_looks, "total_rb_looks": total_rb_looks, "total_wrte_looks": total_wrte_looks, "team": redzone_json[player]["team"], "delta": delta, "delta3": delta3})
	return top_redzone

if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument("-c", "--cron", help="Do Cron job", action="store_true")
	parser.add_argument("-t", "--team", help="Group By Team", action="store_true")
	parser.add_argument("-snaps", "--snaps", help="Snap Trends", action="store_true")
	parser.add_argument("--pretty", help="Pretty Print", action="store_true")
	parser.add_argument("-p", "--pos", help="Filter by Position", default="RB")
	parser.add_argument("-teams", "--teams", help="Filter teams")
	parser.add_argument("-s", "--start", help="Start Week", type=int)
	parser.add_argument("-e", "--end", help="End Week", type=int)

	args = parser.parse_args()
	end_week = 2

	if args.start:
		curr_week = args.start
		end_week = curr_week + 1
		if args.end:
			end_week = args.end

	if args.cron:
		print("WRITING REDZONE")
		write_redzone(curr_week)
		exit()

	top_redzone = get_player_looks_arr(curr_week)

	if args.snaps:
		rbbc_teams = ['crd', 'atl', 'rav', 'buf', 'car', 'chi', 'cin', 'cle', 'dal', 'den', 'det', 'gnb', 'htx', 'clt', 'jax', 'kan', 'sdg', 'ram', 'rai', 'mia', 'min', 'nor', 'nwe', 'nyg', 'nyj', 'phi', 'pit', 'sea', 'sfo', 'tam', 'oti', 'was']

		print("View on [Site](https://zhecht.pythonanywhere.com/rbbc)")
		print("\nWeekly, I'll be posting this backfield analysis alongside my [Redzone Look Trends]() post")
		print("\nNotes:")
		print("\n- Purpose: Examine backfield trends from the previous weeks")
		print("\n- Target Share and RZ Share are only relative to FBs/RBs on the team. Data is adjusted for injuries")
		print("\n- Source: https://www.footballguys.com/stats/redzone/teams?team=NYG&year=2022")
		print("\n- #Reply with a team name if you want to just see their breakdown of W/R/T")

		# uptrend: Singletary, Chubb, Zeke, Jamaal Williams, Pierce, JRob, Etienne, Akers, Edmonds, Rhamondre, Saquon, Breece, Henry
		# Downtrend: Javonte, Mckinnon, Ekeler, Henderson, Mostert, Kamara, Sanders, Gibson
		if args.teams:
			rbbc_teams = args.teams.split(",")

		snap_trends = get_redzone_trends(SNAP_LINKS, curr_week, args.pos)
		for team in SNAP_LINKS:
			team_display = TEAM_TRANS[team] if team in TEAM_TRANS else team
			#team_display = full_team_names[team] if team in full_team_names else team
			print(f"\n#{team_display.upper()}")
			print(f"Player|wk{curr_week} Snap %|RZ Looks Per Game|RZ Looks Share|Targets Per Game|{args.pos} Target Share")
			print(":--|:--|:--|:--|:--|:--")
			extra = ""
			rows = []
			for player in snap_trends[team]:
				#print(player, snap_trends[team][player])
				if snap_trends[team][player]["snaps"] == 0:
					if snap_trends[team][player]["looks_per_game"] == 0 and snap_trends[team][player]["targets_per_game"] == 0:
						continue
					extra += f"{player.title()}|DNP|{snap_trends[team][player]['looks_per_game']}|{snap_trends[team][player]['looks_share']}%|{snap_trends[team][player]['targets_per_game']}|{snap_trends[team][player]['target_share']}%\n"
				else:
					if snap_trends[team][player]["total_looks"] == 0 and snap_trends[team][player]["total_targets"] == 0:
						pass
						#continue

					lastSnaps = snap_trends[team][player]["snaps"]
					avgSnaps = snap_trends[team][player]["avg_snaps"]
					snapsTrend = snap_trends[team][player]["snaps_trend"]
					lpg = snap_trends[team][player]["looks_per_game"]
					lpgTrend = snap_trends[team][player]["looks_per_game_trend"]
					lookShare = snap_trends[team][player]["looks_share"]
					lookShareTrend = snap_trends[team][player]["looks_share_trend"]
					tpg = snap_trends[team][player]["targets_per_game"]
					tpgTrend = snap_trends[team][player]["targets_per_game_trend"]
					tgtShare = snap_trends[team][player]["target_share"]
					tgtShareTrend = snap_trends[team][player]["target_share_trend"]
					# simple print
					#print(f"{player}|{avgSnaps}%|{lpg}|{lookShare}%|{tpg}|{tgtShare}%")
					#print(f"{player}|{avgSnaps}% ({snapsTrend})|{lpg} ({lpgTrend})|{lookShare}% ({lookShareTrend})|{tpg} ({tpgTrend})|{tgtShare}% ({tgtShareTrend})")

					rows.append({
						"player": player,
						#"snaps": avgSnaps,
						"snaps": lastSnaps,
						"text": f"{player.title()}|{lastSnaps}% ({snapsTrend})|{lpg} ({lpgTrend})|{lookShare}% ({lookShareTrend})|{tpg} ({tpgTrend})|{tgtShare}% ({tgtShareTrend})"
					})

			for data in sorted(rows, key=operator.itemgetter("snaps"), reverse=True):
				print(data["text"])
			# print DNP on bottotm
			print(extra)
			# ranks

	elif args.team:
		
		# Team
		team_totals = {}
		for arr in top_redzone:
			if arr["team"] not in team_totals or arr["total_team_looks"] > team_totals[arr["team"]]:
				team_totals[arr["team"]] = arr["total_team_looks"]
		for team in team_totals:
			team_schedule = get_opponents(team)
			tot_games = 0
			for week in range(curr_week):
				if team_schedule[week] != "BYE":
					tot_games += 1
			#print(team, team_totals[team], tot_games)
			team_totals[team] = round(team_totals[team] / float(tot_games), 2)
		team_totals = sorted(team_totals.items(), key=lambda x: x[1], reverse=True)

		print("\nRank|Team|RZ Looks Per Game")
		print(":--|:--|:--")
		idx = 1
		for team, tot in team_totals:
			print(f"{idx}|{full_team_names[team]}|{tot}")
			idx += 1
		# player | redzone looks RB share | snap count
	else:
		sorted_looks = sorted(top_redzone, key=operator.itemgetter("looks_per_game", "looks_perc"), reverse=True)

		sorted_looks_perc = sorted(top_redzone, key=operator.itemgetter("looks_perc"), reverse=True)

		#feelsbad_players = ["amari cooper", "sammy watkins", "stefon diggs", "adam thielen", "calvin ridley", "michael thomas", "odell beckham", "robert woods", "oj howard", "brandin cooks", "robby anderson"]
		feelsbad = {}
		players_on_teams,translations = read_rosters()
		players_on_FA = read_FA()
		players_on_teams = {**players_on_teams, **players_on_FA}
		update_players_on_teams(players_on_teams)

		print("View on [Site](https://zhecht.pythonanywhere.com/redzone)")
		#print("\nView as [Image]()")
		print("\nWeekly, I'll be posting this Redzone Look Trends alongside my [Backfield Trends]() post")
		print("\nNotes:")
		print("\n- Purpose: Track players getting targets + rushes inside the 20 yard line")
		print("\n- Source: https://www.footballguys.com/stats/redzone/teams?team=NYG&year=2022")
		print("\n- #Reply with a team name if you want to just see their breakdown of W/R/T")

		# uptrend: Dameon Pierce, JRob, Singletary, Herbert, Akers, Etienne, Dobbins, Zeke, Zay Jones, DK, Mack Hollins, Kelce, MAndrews, Njoku, Dissly
		# Downtrend: Jeff Wilson, CMC, Javonte, Henderson, Ekeler, Sanders, Pittman, MT, Waller, 
		if 0:
			print("\n#The FeelsBad Table")
			print("\nPlayer|Team|RZ Looks Per Game|1 Week Trend|3 Week Trend|RZ Team Share")
			print(":--|:--|:--|:--|:--|:--")
			for player in sorted_looks:
				#continue

				#if player["looks"] >= 0 and player["name"] in feelsbad_players: 
				if player["team"] == 'tb':
					print(f"{player['name'].title()}|{player['team']}|{player['looks_per_game']}|{player['delta']}|{player['delta3']}|{player['looks_perc']}%")
			exit()

		if 0:
			print("\n#The Julio Jones Table")
			print("\nPlayer|Team|RZ Looks Per Game|1 Week Trend|3 Week Trend|RZ Team Share")
			print(":--|:--|:--|:--|:--|:--")

			for player in sorted_looks:
				#continue
				if player["looks"] >= 0 and player["name"] == "julio jones":
					print(f"{player['name'].title()}|{player['team'].upper()}|{player['looks_per_game']}|{player['delta']}|{player['delta3']}|{player['looks_perc']}%")

		#exit()
		print("\n#Top 50 RB")
		print("\nPlayer|Team|RZ Looks Per Game|1 Week Trend|3 Week Trend|RZ Team Share")
		print(":--|:--|:--|:--|:--|:--")
		printed = 0
		for player in sorted_looks:
			#continue
			if printed == 50:
				break
			if player["looks"] >= 0 and players_on_teams[player["name"]]["position"] == "RB":
				printed += 1
				delta3 = "-" if player["gamesPlayed"] <= 3 else player["delta3"]
				print(f"{player['name'].title()}|{player['team'].upper()}|{player['looks_per_game']}|{player['delta']}|{delta3}|{player['looks_perc']}%")

		print("\n#Top 50 WR")
		print("\nPlayer|Team|RZ Looks Per Game|1 Week Trend|3 Week Trend|RZ Team Share")
		print(":--|:--|:--|:--|:--|:--")
		printed = 0
		for player in sorted_looks:
			#continue
			if printed == 50:
				break
			if player["looks"] >= 0 and players_on_teams[player["name"]]["position"] == "WR":
				printed += 1
				delta3 = "-" if player["gamesPlayed"] <= 3 else player["delta3"]
				print(f"{player['name'].title()}|{player['team'].upper()}|{player['looks_per_game']}|{player['delta']}|{delta3}|{player['looks_perc']}%")

		print("\n#Top 50 TE")
		print("\nPlayer|Team|RZ Looks Per Game|1 Week Trend|3 Week Trend|RZ Team Share")
		print(":--|:--|:--|:--|:--|:--")
		printed = 0
		for player in sorted_looks:
			#continue
			if printed == 50:
				break
				#pass
			if player["looks"] >= 0 and players_on_teams[player["name"]]["position"] == "TE":
				printed += 1
				delta3 = "-" if player["gamesPlayed"] <= 3 else player["delta3"]
				print(f"{player['name'].title()}|{player['team'].upper()}|{player['looks_per_game']}|{player['delta']}|{delta3}|{player['looks_perc']}%")

		
