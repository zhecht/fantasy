from bs4 import BeautifulSoup
from pprint import pprint
import argparse
import os
import json

try:
	from controllers.functions import *
	from controllers.read_rosters import *
	from controllers.reddit import *
	from controllers.snap_stats import *
except:
	from functions import *
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
	"ram": "Rams",
	"nor": "Saints",
	"phi": "Eagles",
	"rai": "Raiders",
	"clt": "Colts",
	"rav": "Ravens",
	"nwe": "Patriots",
	"htx": "Texans",
	"sfo": "49ers",
	"sdg": "Chargers",
	"cin": "Bengals",
	"kan": "Chiefs",
	"atl": "Falcons",
	"pit": "Steelers",
	"den": "Broncos",
	"jax": "Jaguars",
	"det": "Lions",
	"chi": "Bears",
	"gnb": "Packers",
	"nyj": "Jets",
	"nyg": "Giants",
	"oti": "Titans",
	"dal": "Cowboys",
	"min": "Vikings",
	"was": "Washington",
	"tam": "Buccaneers",
	"cle": "Browns",
	"sea": "Seahawks",
	"car": "Panthers",
	"crd": "Cardinals",
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

	#SNAP_LINKS = ["teampage-crd-", "teampage-mia-"]

	for link in SNAP_LINKS:
		link = "{}3.php".format(link)
		base_url = "http://subscribers.footballguys.com/teams/"
		team = link.split('-')[1]

		html = urllib.urlopen(base_url+link)
		soup = BeautifulSoup(html.read(), "lxml")
		rows = soup.find('table', class_='datasmall').find_all('tr')

		saw_QB = False
		total_redzone = 0
		team_total_json[team] = {"RB": [], "WR/TE": []}
		team_total_json[team]["RB"] = [0]*17
		team_total_json[team]["WR/TE"] = [0]*17

		for row in rows[1:]:
			tds = row.find_all('td')
			redzone_counts = []
			which_total = ""
			full_name = ""
			if row.get("bgcolor") is not None:
				which_total = tds[0].find("b").text
			else:
				full = tds[0].find('a').text
				full_name = fixName(full.lower().replace("'", ""))

			for week in range(1,17):
				try:
					perc = int(tds[week].text)
				except:
					perc = 0

				if which_total.find("TOTAL") != -1:
					if which_total.find("QB") == -1:
						if which_total.find("RB") > -1:
							team_total_json[team]["RB"][week - 1] += perc
						else:
							team_total_json[team]["WR/TE"][week - 1] += perc
				else:
					redzone_counts.append(perc)

			if full_name:
				team_ = team
				#if full_name in redzone_json and full_name in nfl_trades:
				#	team_ = nfl_trades[full_name]["team"]
				#	looks = redzone_json[full_name]["looks"].split(",")
				#	redzone_counts = [ val + int(looks[idx]) for idx, val in enumerate(redzone_counts) ]
				if full_name in nfl_trades:
					if nfl_trades[full_name]["team"] == team:
						redzone_json[full_name] = {"looks": ','.join(str(x) for x in redzone_counts), "team": team_, "looks_perc": ""}
				else:
					redzone_json[full_name] = {"looks": ','.join(str(x) for x in redzone_counts), "team": team_, "looks_perc": ""}
	
	for player in redzone_json:
		perc_arr = []
		for week in range(1,17):
			team = redzone_json[player]["team"]
			if player in nfl_trades:
				if week < nfl_trades[player]["week"]:
					team = nfl_trades[player]["from"]
				else:
					team = nfl_trades[player]["team"]
			looks = [int(x) for x in redzone_json[player]["looks"].split(",")]
			team_total_rb = team_total_json[team]["RB"][week - 1]
			team_total_wrte = team_total_json[team]["WR/TE"][week - 1]
			perc = 0 if team_total_rb + team_total_wrte == 0 else (looks[week - 1] / float(team_total_rb + team_total_wrte))
			perc_arr.append(round(perc, 2))

		redzone_json[player]["looks_perc"] = ','.join(str(x) for x in perc_arr)

	new_j = {}
	for player in redzone_json:
		new_name = player.lower().replace("'", "").replace(".", "")
		new_j[new_name] = redzone_json[player].copy()

		if new_name.split(" ")[-1] in ["jr", "iii", "ii", "sr", "v"]:
			new_name = " ".join(new_name.split(" ")[:-1])
			new_j[new_name] = redzone_json[player].copy()

	redzone_json = merge_two_dicts(new_j, redzone_json)

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

def get_redzone_trends(rbbc_teams, curr_week=1, requested_pos="RB", is_ui=False):
	redzone_json = read_redzone()
	team_total_json = read_team_total()
	players_on_teams,translations = read_rosters()
	players_on_FA = read_FA()
	snap_stats = read_snap_stats(curr_week)
	target_stats = read_target_stats()
	#players_on_teams = {**players_on_teams, **players_on_FA}
	players_on_teams = merge_two_dicts(players_on_teams, players_on_FA)
	update_players_on_teams(players_on_teams)
	trends = {}
	for player in snap_stats:
		if player not in redzone_json:
			continue
		if player not in players_on_teams or players_on_teams[player]["position"] == "QB":
			continue

		pos = players_on_teams[player]["position"]
		team = redzone_json[player]["team"]

		if pos in requested_pos.split("/") and (len(rbbc_teams) == 0 or team in rbbc_teams):
			if team not in trends:
				trends[team] = {}
			if player not in trends[team]:
				trends[team][player] = {
					"snaps": snap_stats[player]["perc"],
					"looks": redzone_json[player]["looks"],
					"targets": target_stats[player]["counts"],
					"total_targets": sum(map(int, target_stats[player]["counts"].split(","))),
					"total_looks": sum(map(int, redzone_json[player]["looks"].split(",")))
				}
	
	redzone_totals = get_redzone_totals(curr_week, trends, snap_stats, team_total_json, requested_pos)
	target_aggregates = get_target_aggregate_stats(curr_week)

	#print(redzone_totals["oti"])
	for team in trends:
		total_looks = team_total_json[team][requested_pos][curr_week - 1]

		for player in trends[team]:
			looks_arr = trends[team][player]["looks"].split(",")
			targets_arr = trends[team][player]["targets"].split(",")
			looks_per_game, last_looks_per_game, last_3_looks_per_game = get_looks_per_game(player, curr_week, looks_arr, snap_stats)
			targets_per_game, last_targets_per_game, last_3_targets_per_game = get_targets_per_game(player, curr_week, targets_arr, snap_stats)
			snaps_per_game, last_snaps_per_game, last_3_snaps_per_game = get_snaps_per_game(player, curr_week, snap_stats)

			rz = int(trends[team][player]["looks"].split(",")[curr_week - 1])
			last_rz = int(trends[team][player]["looks"].split(",")[curr_week - 1])
			last_snaps = float(trends[team][player]["snaps"].split(",")[curr_week - 1])
			#if player == "leveon bell":
			#	print(target_aggregates[player])
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
				
				try:			
					last_looks_perc = round(float(redzone_totals[player]["last_total"] / redzone_totals[team]["last_total"]) * 100, 1)
				except:
					last_looks_perc = 0
				try:
					last_target_share = round(float(target_aggregates[player]["perc"].split(",")[curr_week - 2]) * 100, 1)
				except:
					last_target_share = 0

			snaps_trend = round(snaps_per_game - avg_snaps, 1)
			looks_trend = int(trends[team][player]["looks"].split(",")[curr_week - 1])
			target_trend = int(trends[team][player]["targets"].split(",")[curr_week - 1])
			looks_share_trend = round(looks_perc - last_looks_perc, 1)
			target_share_trend = round(target_share - last_target_share, 1)
			looks_per_game_trend = round(looks_per_game - last_looks_per_game, 2)
			targets_per_game_trend = round(targets_per_game - last_targets_per_game, 2)

			snaps_per_game_trend = round(snaps_per_game - last_snaps_per_game, 2)

			trends[team][player]["looks_per_game"] = looks_per_game
			trends[team][player]["targets_per_game"] = targets_per_game
			trends[team][player]["looks_share"] = looks_perc
			trends[team][player]["snaps"] = last_snaps
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

def get_looks_per_game(player, curr_week, looks_arr, snap_stats):
	tot_games = 0
	tot_looks = 0
	looks_per_game = 0
	last_looks_per_game = 0
	last_3_looks_per_game = 0
	for week in range(0, curr_week):
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

		for week in range(1, curr_week + 1):
			if player not in snap_stats or int(snap_stats[player]["counts"].split(",")[week - 1]) == 0:
				continue

			looks = int(looks_arr[week - 1])
			looks_perc = float(looks_perc_arr[week - 1])
			total_rb_looks += team_total_json[redzone_json[player]["team"]]["RB"][week - 1]
			total_wrte_looks += team_total_json[redzone_json[player]["team"]]["WR/TE"][week - 1]
			total_player_looks += looks

		looks_per_game, last_looks_per_game, last_3_looks_per_game = get_looks_per_game(player, curr_week, looks_arr, snap_stats)

		total_team_looks = total_rb_looks + total_wrte_looks
		#if redzone_json[player]["team"] == "sea":
		#	print(player, week, total_team_looks)

		last_total_team_looks = total_team_looks - team_total_json[redzone_json[player]["team"]]["RB"][curr_week - 1] - team_total_json[redzone_json[player]["team"]]["WR/TE"][curr_week - 1]
		
		last_3_total_team_looks = last_total_team_looks - team_total_json[redzone_json[player]["team"]]["RB"][curr_week - 2] - team_total_json[redzone_json[player]["team"]]["WR/TE"][curr_week - 2] - team_total_json[redzone_json[player]["team"]]["RB"][curr_week - 3] - team_total_json[redzone_json[player]["team"]]["WR/TE"][curr_week - 3]

		try:
			looks_perc = round((float(total_player_looks) / total_team_looks) * 100, 2)
			if curr_week >= 2:
				last_looks_perc = round((float(total_player_looks - int(looks_arr[curr_week - 1])) / last_total_team_looks) * 100, 2)
			else:
				last_looks_perc = looks_perc if curr_week == 1 else 0
			last_3_looks_perc = looks_perc if curr_week == 1 else 0
			if curr_week >= 4:
				last_3_looks_perc = round((float(total_player_looks - int(looks_arr[curr_week - 3]) - int(looks_arr[curr_week - 2]) - int(looks_arr[curr_week - 1])) / last_3_total_team_looks) * 100, 2)
			else:
				last_3_looks_perc = looks_perc if curr_week == 1 else 0
		except:
			#print(player, total_team_looks, last_total_team_looks, last_3_total_team_looks)
			continue

		delta = round(looks_per_game - last_looks_per_game, 2)
		delta3 = round(looks_per_game - last_3_looks_per_game, 2)
		if is_ui:
			if delta == 0:
				delta = "-"
			else:
				delta = f"+{delta}" if delta > 0 else f"{delta}"
			if delta3:
				delta3 = f"+{delta3}" if delta3 > 0 else f"{delta3}"
			else:
				delta3 = "-"
		else:
			if delta == 0:
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
			top_redzone.append({"name": player, "looks_per_game": looks_per_game, "looks": total_player_looks, "looks_perc": looks_perc, "total_team_looks": total_team_looks, "total_rb_looks": total_rb_looks, "total_wrte_looks": total_wrte_looks, "team": redzone_json[player]["team"], "delta": delta, "delta3": delta3})
	return top_redzone

SNAP_LINKS = [ "teampage-atl-", "teampage-buf-", "teampage-car-", "teampage-chi-", "teampage-cin-", "teampage-cle-", "teampage-clt-", "teampage-crd-", "teampage-dal-", "teampage-den-", "teampage-det-", "teampage-gnb-", "teampage-htx-", "teampage-jax-", "teampage-kan-", "teampage-mia-", "teampage-min-", "teampage-nor-", "teampage-nwe-", "teampage-nyg-", "teampage-nyj-", "teampage-oti-", "teampage-phi-", "teampage-pit-", "teampage-rai-", "teampage-ram-", "teampage-rav-", "teampage-sdg-", "teampage-sea-", "teampage-sfo-", "teampage-tam-", "teampage-was-" ]

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
		team_trans = {"rav": "bal", "htx": "hou", "oti": "ten", "sdg": "lac", "ram": "lar", "clt": "ind", "crd": "ari", "gnb": "gb", "kan": "kc", "nwe": "ne", "rai": "lv", "sfo": "sf", "tam": "tb", "nor": "no"}
		rbbc_teams = ['crd', 'atl', 'rav', 'buf', 'car', 'chi', 'cin', 'cle', 'dal', 'den', 'det', 'gnb', 'htx', 'clt', 'jax', 'kan', 'sdg', 'ram', 'rai', 'mia', 'min', 'nor', 'nwe', 'nyg', 'nyj', 'phi', 'pit', 'sea', 'sfo', 'tam', 'oti', 'was']

		print("View on [Site](https://zhecht.pythonanywhere.com/rbbc)")
		print("\nWeekly, I'll be posting this RBBC analysis alongside my [Redzone Look Trends]() post")
		print("\nNotes:")
		print("\n- Purpose: Examine backfield trends from the previous weeks")
		print("\n- Target Share and RZ Share are only relative to FBs/RBs on the team. Data is adjusted for injuries")
		print("\n- Source: https://subscribers.footballguys.com/teams/teampage-den-3.php")
		print("\n- #Reply with a team name if you want to just see their breakdown of W/R/T")

		if args.teams:
			rbbc_teams = args.teams.split(",")
		snap_trends = get_redzone_trends(rbbc_teams, curr_week, args.pos)
		for team in rbbc_teams:
			team_display = team_trans[team] if team in team_trans else team
			#team_display = full_team_names[team] if team in full_team_names else team
			print(f"\n#{team_display.upper()}")
			print("Player|AVG Snap %|RZ Looks Per Game|RZ Looks Share|Targets Per Game|{} Target Share".format(args.pos))
			print(":--|:--|:--|:--|:--|:--")
			extra = ""
			for player in snap_trends[team]:
				#print(player, snap_trends[team][player])
				if snap_trends[team][player]["snaps"] == 0:
					if snap_trends[team][player]["looks_per_game"] == 0 and snap_trends[team][player]["targets_per_game"] == 0:
						continue
					extra += f"{player}|DNP|{snap_trends[team][player]['looks_per_game']}|{snap_trends[team][player]['looks_share']}%|{snap_trends[team][player]['targets_per_game']}|{snap_trends[team][player]['target_share']}%\n"
				else:
					if snap_trends[team][player]["total_looks"] == 0 and snap_trends[team][player]["total_targets"] == 0:
						pass
						#continue

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
					print(f"{player}|{avgSnaps}% ({snapsTrend})|{lpg} ({lpgTrend})|{lookShare}% ({lookShareTrend})|{tpg} ({tpgTrend})|{tgtShare}% ({tgtShareTrend})")
			# print DNP on bottotm
			print(extra)
			# ranks

	elif args.team:
		
		# Team
		team_totals = {}
		for arr in top_redzone:
			if arr["team"] not in team_totals or arr["total_team_looks"] > team_totals[arr["team"]]:
				team_totals[arr["team"]] = arr["total_team_looks"]
		import profootballreference
		for team in team_totals:
			team_schedule = profootballreference.get_opponents(team)
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
		print("\nView as [Image]()")
		print("\nWeekly, I'll be posting this Redzone Look Trends alongside my [Backfield Trends]() post")
		print("\nNotes:")
		print("\n- Purpose: Track players getting targets or rushes inside the 20 yard line")
		print("\n- Source: https://subscribers.footballguys.com/teams/teampage-den-6.php")
		print("\n- #Reply with a team name if you want to just see their breakdown of W/R/T")

		print("\n#The FeelsBad Table")
		print("\nPlayer|RZ Looks Per Game|1 Week Trend|3 Week Trend|RZ Team Share")
		print(":--|:--|:--|:--|:--")
		for player in sorted_looks:
			continue

			#if player["looks"] >= 0 and player["name"] in feelsbad_players: 
			if player["team"] == 'buf':
				print(f"{player['name'].title()}|{player['looks_per_game']}|{player['delta']}|{player['looks_perc']}%")
		#exit()

		print("\n#The Julio Jones Table")
		print("\nPlayer|RZ Looks Per Game|1 Week Trend|3 Week Trend|RZ Team Share")
		print(":--|:--|:--|:--|:--")
		
		for player in sorted_looks:
			#continue
			if player["looks"] >= 0 and player["name"] == "julio jones":
				print(f"{player['name'].title()}|{player['looks_per_game']}|{player['delta']}|{player['delta3']}|{player['looks_perc']}%")

		#exit()
		print("\n#Top 50 RB")
		print("\nPlayer|RZ Looks Per Game|1 Week Trend|3 Week Trend|RZ Team Share")
		print(":--|:--|:--|:--|:--")
		printed = 0
		for player in sorted_looks:
			#continue
			if printed == 50:
				break
			if player["looks"] >= 0 and players_on_teams[player["name"]]["position"] == "RB":
				printed += 1
				print(f"{player['name'].title()}|{player['looks_per_game']}|{player['delta']}|{player['delta3']}|{player['looks_perc']}%")

		print("\n#Top 50 WR")
		print("\nPlayer|RZ Looks Per Game|1 Week Trend|3 Week Trend|RZ Team Share")
		print(":--|:--|:--|:--|:--")
		printed = 0
		for player in sorted_looks:
			#continue
			if printed == 50:
				break
			if player["looks"] >= 0 and players_on_teams[player["name"]]["position"] == "WR":
				printed += 1
				print(f"{player['name'].title()}|{player['looks_per_game']}|{player['delta']}|{player['delta3']}|{player['looks_perc']}%")

		print("\n#Top 40 TE")
		print("\nPlayer|RZ Looks Per Game|1 Week Trend|3 Week Trend|RZ Team Share")
		print(":--|:--|:--|:--|:--")
		printed = 0
		for player in sorted_looks:
			#continue
			if printed == 40:
				break
			if player["looks"] >= 0 and players_on_teams[player["name"]]["position"] == "TE":
				printed += 1
				print(f"{player['name'].title()}|{player['looks_per_game']}|{player['delta']}|{player['delta3']}|{player['looks_perc']}%")

		
