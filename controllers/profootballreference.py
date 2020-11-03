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
from sys import platform
from subprocess import call
from glob import glob

try:
  import urllib2 as urllib
except:
  import urllib.request as urllib

prefix = ""
if os.path.exists("/home/zhecht/fantasy"):
	prefix = "/home/zhecht/fantasy/"

def merge_two_dicts(x, y):
	z = x.copy()
	z.update(y)
	return z

def get_abbr(team):
	if team == "ari":
		return "crd"
	elif team == "bal":
		return "rav"
	elif team == "hou":
		return "htx"
	elif team == "ind":
		return "clt"
	elif team == "lac":
		return "sdg"
	elif team == "lar":
		return "ram"
	elif team == "lvr":
		return "rai"
	elif team == "ten":
		return "oti"
	elif team == "tb":
		return "tam"
	elif team == "no":
		return "nor"
	elif team == "gb":
		return "gnb"
	elif team == "sf":
		return "sfo"
	elif team == "ne":
		return "nwe"
	return team

def get_default(key):
	# return default
	if key in ["rush_yds", "rec_yds"]:
		return 0.1
	elif key in ["pass_yds"]:
		return 0.04
	elif key == "ppr":
		return 0.5
	elif key in ["rush_td", "rec_td"]:
		return 6
	elif key in ["pass_td"]:
		return 4
	elif key in ["fumbles_lost", "pass_int"]:
		return -2
	elif key in ["xpm"]:
		return 1
	return 0

def get_points(key, val, settings):
	if key == "rec":
		key = "ppr"
	multiply = settings[key] if key in settings else get_default(key)
	if key in settings and key in ["rush_yds", "rec_yds", "pass_yds"]:
		multiply = 1.0 / multiply

	if key == "fg_made":
		pts = 0
		for fg in val:
			if int(fg) >= 50:
				pts += settings["field_goal_50+"] if "field_goal_50+" in settings else 5
			elif int(fg) >= 40:
				pts += settings["field_goal_40-49"] if "field_goal_40-49" in settings else 4
			elif int(fg) >= 30:
				pts += settings["field_goal_30-39"] if "field_goal_30-39" in settings else 3
			elif int(fg) >= 20:
				pts += settings["field_goal_20-29"] if "field_goal_20-29" in settings else 3
			else:
				pts += settings["field_goal_0-19"] if "field_goal_0-19" in settings else 3
		return pts
	return val * multiply
	return 0

def get_points_from_PA(pts_allowed, settings):
	points = settings["0_points_allowed"] if "0_points_allowed" in settings else 10
	if pts_allowed >= 1 and pts_allowed <= 6:
		points = settings["1-6_points_allowed"] if "1-6_points_allowed" in settings else 7
	elif pts_allowed >= 7 and pts_allowed <= 13:
		points = settings["7-13_points_allowed"] if "7-13_points_allowed" in settings else 4
	elif pts_allowed >= 14 and pts_allowed <= 20:
		points = settings["14-20_points_allowed"] if "14-20_points_allowed" in settings else 1
	elif pts_allowed >= 21 and pts_allowed <= 27:
		points = settings["21-27_points_allowed"] if "21-27_points_allowed" in settings else 0
	elif pts_allowed >= 28 and pts_allowed <= 34:
		points = settings["28-34_points_allowed"] if "28-34_points_allowed" in settings else -1
	elif pts_allowed >= 35:
		points = settings["35+_points_allowed"] if "35+_points_allowed" in settings else -4
	return points

def calculate_defense_points(stats, settings):
	pts_allowed = stats["rush_td"]*6 + stats["pass_td"]*6 + stats["xpm"] + stats["fgm"]*3 + stats["2pt_conversions"]*2
	points = get_points_from_PA(pts_allowed, settings)
	points += (stats["kick_ret_td"] * 6)
	points += (stats["punt_ret_td"] * 6)
	
	multiply = settings["interception"] if "interception" in settings else 2
	points += (stats["pass_int"] * multiply)
	
	multiply = settings["fumble_recovery"] if "fumble_recovery" in settings else 2
	points += (stats["fumbles_lost"] * multiply)

	multiply = settings["safety"] if "safety" in settings else 2
	points += (stats["safety"] * multiply)

	multiply = settings["touchdown"] if "touchdown" in settings else 6
	points += (stats["def_tds"] * multiply)

	multiply = settings["sack"] if "sack" in settings else 1
	points += (stats["pass_sacked"] * multiply)
	return points

def calculate_aggregate_stats(settings=None):
	if not settings:
		settings = {"ppr": 0.5}
	test_settings = settings.copy()
	teamlinks = {}
	with open("{}static/profootballreference/teams.json".format(prefix)) as fh:
		teamlinks = json.loads(fh.read())
	
	for team in teamlinks:
		stats = {}
		path = "{}static/profootballreference/{}".format(prefix, team.split("/")[-2])
		files = glob("{}/wk*.json".format(path))
		for f in files:
			m = re.search(r'wk(\d+).json', f)
			week = m.group(1)
			team_stats = {}
			with open(f) as fh:
				team_stats = json.loads(fh.read())

			for player in team_stats:
				if player not in stats:
					stats[player] = {"tot": {"standard_points": 0, "half_points": 0, "full_points": 0}}
				if "wk{}".format(week) not in stats[player]:
					stats[player]["wk{}".format(week)] = {}

				points = 0
				points_arr = {"standard": 0, "half": 0, "full": 0}
				for player_stats_str in team_stats[player]:
					if player_stats_str not in stats[player]["tot"]:
						if player_stats_str == "fg_made":
							stats[player]["tot"][player_stats_str] = []
						else:
							stats[player]["tot"][player_stats_str] = 0
					stats[player]["wk{}".format(week)][player_stats_str] = team_stats[player][player_stats_str]
					if player_stats_str == "fg_made":
						stats[player]["tot"][player_stats_str].extend(team_stats[player][player_stats_str])
					else:
						stats[player]["tot"][player_stats_str] += team_stats[player][player_stats_str]

					if player_stats_str == "rec":
						test_settings["ppr"] = 0
						points_arr["standard"] += get_points(player_stats_str, team_stats[player][player_stats_str], test_settings)
						test_settings["ppr"] = 0.5
						points_arr["half"] += get_points(player_stats_str, team_stats[player][player_stats_str], test_settings)
						test_settings["ppr"] = 1
						points_arr["full"] += get_points(player_stats_str, team_stats[player][player_stats_str], test_settings)
					else:
						points += get_points(player_stats_str, team_stats[player][player_stats_str], settings)
				# calculate def points
				for s in ["standard", "half", "full"]:
					pts = round(points + points_arr[s], 2)
					if player == "OFF":
						pts = calculate_defense_points(team_stats[player], settings)
					stats[player]["wk{}".format(week)]["{}_points".format(s)] = pts
					stats[player]["tot"]["{}_points".format(s)] += pts
			
		with open("{}/stats.json".format(path), "w") as fh:
			json.dump(stats, fh, indent=4)

# return (in order) list of opponents
def get_opponents(team):
	team = get_abbr(team)
	schedule = {}
	with open("{}static/profootballreference/schedule.json".format(prefix)) as fh:
		schedule = json.loads(fh.read())
	opps = []
	for i in range(1, 18):
		opp_team = "BYE"
		for games in schedule[str(i)]:
			away, home = games.split(" @ ")
			if away == team:
				opp_team = home
			elif home == team:
				opp_team = away
		opps.append(opp_team)
	return opps


# read rosters and return ARRAY of players on team playing POS 
def get_players_by_pos_team(team, pos):
	nfl_trades = read_nfl_trades()
	roster = {}
	if team == "BYE":
		return []
	with open("{}static/profootballreference/{}/roster.json".format(prefix, team)) as fh:
		roster = json.loads(fh.read())
	arr = []
	for player in roster:
		if roster[player].lower() == pos.lower():
			arr.append(player)
	for player in nfl_trades:
		if nfl_trades[player]["from"] == team:
			opp_roster = {}
			with open("{}static/profootballreference/{}/roster.json".format(prefix, nfl_trades[player]["team"])) as fh:
				opp_roster = json.loads(fh.read())
			if opp_roster[player].lower() == pos.lower():
				arr.append(player)
	# IR is not listed on roster
	ir_data = [
		("nwe", "QB", "cam newton"),
		("dal", "QB", "dak prescott"),
		("nwe", "RB", "sony michel"),
		("nyg", "RB", "saquon barkley"),
		("sfo", "RB", "tevin coleman"),
		("sdg", "RB", "austin ekeler"),
		("car", "RB", "christian mccaffrey"),
		("ram", "RB", "cam akers"),
		("cle", "RB", "nick chubb"),
		("ind", "WR", "parris campbell"),
		("den", "WR", "courtland sutton"),
		("gnb", "WR", "allen lazard"),
		("phi", "WR", "jalen reagor"),
		("nyg", "WR", "sterling shepard"),
		("nyg", "WR", "golden tate"),
		("nyg", "WR", "kaden smith"),
		("nyg", "WR", "cj board"),
		("crd", "TE", "dan arnold"),
		("phi", "TE", "dallas goedert"),
		("dal", "TE", "blake jarwin"),
		("cle", "TE", "david njoku"),
		("cin", "TE", "cj uzomah"),
		("jax", "K", "brandon wright"),
		("jax", "K", "josh lambo"),
		("cle", "K", "austin seibert")
	]
	for data in ir_data:
		if team == data[0] and pos == data[1] and data[2] not in arr:
			arr.append(data[2])
	return arr

def get_tot_team_games(curr_week, schedule):
	j = {}
	for i in range(1, curr_week + 1):
		games = schedule[str(i)]
		for game in games:
			t1,t2 = game.split(" @ ")
			if t1 not in j:
				j[t1] = 0
			if t2 not in j:
				j[t2] = 0
			j[t1] += 1
			j[t2] += 1
	return j

def get_point_totals(curr_week, settings, over_expected):
	teams = os.listdir("{}static/profootballreference".format(prefix))
	scoring_key = "half"
	all_team_stats = {}
	projections = {}
	# read all team stats into { team -> player -> [tot, wk1, wk2]}
	for team in teams:
		if team.find("json") >= 0:
			continue
		stats = {}
		with open(f"{prefix}static/profootballreference/{team}/stats.json") as fh:
			all_team_stats[team] = json.load(fh).copy()
		if over_expected:
			with open(f"{prefix}static/projections/projections.json") as fh:
				projections[team] = json.load(fh).copy()
	ranks = []
	for team in all_team_stats:
		pos_tot = {}
		for pos in ["QB", "RB", "WR", "TE", "K", "DEF"]:
			pos_tot[pos] = {}
			players = get_players_by_pos_team(team, pos)
			
			if pos == "DEF":
				players = ["OFF"]
			for player in players:
				if pos != "DEF" and player not in all_team_stats[team]:
					continue
				for wk in all_team_stats[team][player]: # tot, wk1, wk2
					try:
						if int(wk.split("wk")[-1]) > curr_week:
							continue
					except:
						pass
					if wk not in pos_tot[pos]:
						pos_tot[pos][wk] = 0
						pos_tot[pos][wk+"_proj"] = 0
						pos_tot[pos][wk+"_act"] = 0
					
					# don't add if this player had 0 snaps
					if pos not in ["K", "DEF"] and ("snap_counts" not in all_team_stats[team][player][wk] or not all_team_stats[team][player][wk]["snap_counts"]):
						continue
					
					real_pts = 0
					if player == "OFF":
						real_pts = calculate_defense_points(all_team_stats[team][player][wk], settings)
						if over_expected:
							if wk == "tot":
								pass
							elif projections[team][team][wk]:
								real_pts = (real_pts / projections[team][team][wk]) - 1
								real_pts *= 100
								pos_tot[pos][wk+"_proj"] += projections[team][team][wk]
								pos_tot[pos][wk+"_act"] += all_team_stats[team][player][wk]["half_points"]
					elif over_expected:
						if wk == "tot" or player not in projections[team] or wk not in projections[team][player] or not projections[team][player][wk]:
							pass
							#real_pts = all_team_stats[team][player][wk]
						else:
							real_pts = (all_team_stats[team][player][wk]["half_points"] / projections[team][player][wk]) - 1
							real_pts *= 100
							pos_tot[pos][wk+"_proj"] += projections[team][player][wk]
							pos_tot[pos][wk+"_act"] += all_team_stats[team][player][wk]["half_points"]
							#if team == "atl" and pos == "K":
							#	print(player, wk, all_team_stats[team][player][wk]["half_points"], projections[team][player][wk], real_pts)
					else:
						real_pts = get_points_from_settings(all_team_stats[team][player][wk], settings)
					pos_tot[pos][wk] += real_pts
					#pos_tot[pos][wk] += all_team_stats[team][player][wk]["half_points"]
		j = { "team": team }
		for pos in pos_tot:
			#if "{}_tot".format(pos) not in j:
				#j["{}_tot".format(pos)] = 0
			for wk in range(1, curr_week + 1):
				if "wk{}".format(wk) not in pos_tot[pos]: # game hasn't played
					j["{}_wk{}".format(pos, wk)] = 0
				elif f"wk{wk}_proj" in pos_tot[pos] and pos_tot[pos][f"wk{wk}_proj"]:
					j[f"{pos}_wk{wk}_proj"] = pos_tot[pos][f"wk{wk}_proj"]
					j[f"{pos}_wk{wk}_act"] = pos_tot[pos][f"wk{wk}_act"]
					j[f"{pos}_wk{wk}"] = round(((pos_tot[pos][f"wk{wk}_act"] / pos_tot[pos][f"wk{wk}_proj"]) - 1) * 100, 2)
				else:
					j["{}_wk{}".format(pos, wk)] = round(pos_tot[pos]["wk{}".format(wk)], 2)
					#j["{}_tot".format(pos)] += pos_tot[pos]["wk{}".format(wk)]
			#j["{}_tot".format(pos)] = round(j["{}_tot".format(pos)], 2)
		ranks.append(j)
	return ranks


def read_schedule():
	with open("{}static/profootballreference/schedule.json".format(prefix)) as fh:
		j = json.loads(fh.read())
	return j

def read_nfl_trades():
	with open("{}static/nfl_trades.json".format(prefix)) as fh:
		returned_json = json.loads(fh.read())
	return returned_json

def get_defense_tot(curr_week, point_totals_dict, over_expected):
	defense_tot = []
	schedule = read_schedule()
	tot_team_games = get_tot_team_games(curr_week, schedule)
	teams = os.listdir("{}static/profootballreference".format(prefix))
	for team in teams:
		if team.find("json") >= 0:
			continue
		# get opp schedule
		j = {"team": team}
		opponents = get_opponents(team)[:curr_week]
		for week, opp_team in enumerate(opponents):
			for pos in ["QB", "RB", "WR", "TE", "K", "DEF"]:
				key = f"{pos}_wk{week+1}"
				tot_key = f"{pos}_tot"
				act_key = f"{pos}_act"
				proj_key = f"{pos}_proj"
				for k in [key, tot_key, act_key, proj_key]:
					if k not in j:
						j[k] = 0
				if opp_team != "BYE":
					which_team = opp_team
					if pos == "DEF":
						which_team = team
					if over_expected:
						# we calculate the stats for other defenses. No need to iterate over opp_team
						#print(which_team, pos, week)
						j[act_key] += point_totals_dict[which_team][f"{pos}_wk{week+1}_act"]
						j[proj_key] += point_totals_dict[opp_team][f"{pos}_wk{week+1}_proj"]
						j[key] += point_totals_dict[which_team][key]
						j[tot_key] += point_totals_dict[which_team][key]
					else:
						j[key] += point_totals_dict[which_team][key]
						j[tot_key] += point_totals_dict[which_team][key]
						
		for pos in ["QB", "RB", "WR", "TE", "K", "DEF"]:
			games = tot_team_games[team]
			if over_expected and j[f"{pos}_proj"]:
				j[f"{pos}_ppg"] = round(((j[f"{pos}_act"] / j[f"{pos}_proj"]) - 1) * 100, 2)
			else:
				j[f"{pos}_ppg"] = round(j[f"{pos}_tot"] / games, 2)
		defense_tot.append(j)
	return defense_tot

# get rankns of teeams sorted by highest fantasy points scored
def get_ranks(curr_week, settings, over_expected):
	ranks = {}
	point_totals = get_point_totals(curr_week, settings, over_expected)
	for pos in ["QB", "RB", "WR", "TE", "K", "DEF"]:
		for week in range(1, curr_week + 1):
			key = "{}_wk{}".format(pos, week)
			# storred like RB_wk3, etc
			sorted_ranks = sorted(point_totals, key=operator.itemgetter(key), reverse=True)
			for idx, arr in enumerate(sorted_ranks):
				if arr["team"] not in ranks:
					ranks[arr["team"]] = {"RB": {}, "WR": {}, "TE": {}, "QB": {}, "K": {}, "DEF": {}}
				ranks[arr["team"]][pos]["wk{}".format(week)] = idx + 1

	# total opponent's numbers for DEFENSE outlooks
	point_totals_dict = {}
	for arr in point_totals:
		point_totals_dict[arr["team"]] = arr.copy()
	defense_tot = get_defense_tot(curr_week, point_totals_dict, over_expected)

	for pos in ["QB", "RB", "WR", "TE", "K", "DEF"]:
		sorted_ranks = sorted(defense_tot, key=operator.itemgetter("{}_tot".format(pos)), reverse=True)
		for idx, arr in enumerate(sorted_ranks):
			ranks[arr["team"]][pos]["tot"] = idx + 1

	return ranks, defense_tot


def get_pretty_stats(stats, pos, settings):
	#s = "{} PTS - {}".format(stats["points"], player.title())
	s = ""
	if not stats:
		return s
	pos = pos.upper()
	if pos != "K" and "snap_counts" in stats and not stats["snap_counts"]:
		s += "-"
	elif pos == "QB":
		s = "-"
		if "pass_att" in stats:
			s = "{}/{} {} Pass Yds".format(stats["pass_cmp"], stats["pass_att"], stats["pass_yds"])
			if stats["pass_td"]:
				s += ", {} Pass TD".format(stats["pass_td"])
			if stats["pass_int"]:
				s += ", {} Int".format(stats["pass_int"])
	elif pos in ["WR", "TE"]:
		if "targets" in stats and stats["targets"]:
			s = "{}/{} {} Rec Yds".format(stats["rec"], stats["targets"], stats["rec_yds"])
			if stats["rec_td"]:
				s += " {} Rec TD".format(stats["rec_td"])
		else:
			s = "0 Targets"
	elif pos == "K":
		if "fg_made" not in stats:
			s = "{} XP / {} FG made".format(stats["xpm"], stats["fgm"])
		elif "xpm" in stats:
			s = "{} XP / {} FG made {}".format(stats["xpm"], stats["fgm"], stats["fg_made"])
	elif pos == "DEF":
		pts_allowed = stats["rush_td"]*6 + stats["pass_td"]*6 + stats["xpm"] + stats["fgm"]*3 + stats["2pt_conversions"]*2
		s += "{} pts allowed".format(pts_allowed)
		if stats["pass_int"]:
			s += " / {} Int".format(stats["pass_int"])
		if stats["pass_sacked"]:
			plural = "s" if stats["pass_sacked"] > 1 else ""
			s += " / {} Sack{}".format(stats["pass_sacked"], plural)
		if stats["fumbles_lost"]:
			plural = "s" if stats["fumbles_lost"] > 1 else ""
			s += " / {} Fumble{}".format(stats["fumbles_lost"], plural)
		if stats["safety"]:
			s += " / {} Safety".format(stats["safety"])
		if stats["def_tds"]:
			s += " / {} Def TDs".format(stats["def_tds"])
	else: # RB
		s = "0 Rush Yds"
		if "rush_yds" in stats and "rec_yds" in stats:
			s = "{} Rush Yds".format(stats["rush_yds"])
			if stats["rush_td"]:
				s += ", {} Rush TD".format(stats["rush_td"])
			if stats["rec"]:
				s += ", {} Rec, {} Rec Yds".format(stats["rec"], stats["rec_yds"])
			if stats["rec_td"]:
				s += ", {} Rec TD".format(stats["rec_td"])
	return s

team_trans = {"rav": "bal", "htx": "hou", "oti": "ten", "sdg": "lac", "ram": "lar", "rai": "oak", "clt": "ind", "crd": "ari"}

def get_suffix(num):
	if num >= 11 and num <= 13:
		return "th"
	elif num % 10 == 1:
		return "st"
	elif num % 10 == 2:
		return "nd"
	elif num % 10 == 3:
		return "rd"
	return "th"

def get_points_from_settings(stats, settings):
	points = 0
	for s in stats:
		if s.find("points") >= 0:
			continue
		points += get_points(s, stats[s], settings)
	return points

# Given a team, show stats from other players at the same pos 
def position_vs_opponent_stats(team, pos, ranks, settings=None):

	opp_stats = []
	tot_stats = {"points": 0, "stats": {}, "title": "TOTAL vs. {}".format(pos.upper())}
	team = get_abbr(team)
	team_schedule = get_opponents(team)
	scoring_key = "half"
	if settings:
		if settings["ppr"] == 0:
			scoring_key = "standard"
		elif settings["ppr"] == 1:
			scoring_key = "full"
	for idx, opp_team in enumerate(team_schedule):        
		week = idx + 1
		if opp_team == "BYE":
			opp_stats.append({"week": week, "players": "", "team": team})
			continue
		if pos == "DEF":
			path = "{}static/profootballreference/{}".format(prefix, team)
		else:
			path = "{}static/profootballreference/{}".format(prefix, opp_team)
		team_stats = {}
		with open("{}/stats.json".format(path)) as fh:
			team_stats = json.loads(fh.read())

		if pos == "DEF":
			players_arr = ["OFF"]
		else:
			players_arr = get_players_by_pos_team(opp_team, pos)
		display_team = team_trans[team] if team in team_trans else team
		display_opp_team = team_trans[opp_team] if opp_team in team_trans else opp_team
		
		j = {
			"title": "<i style='text-decoration:underline;'>{} vs. {} {}</i>".format(
				display_team.upper(),
				display_opp_team.upper(),
				pos.upper()
			),
			"week": week,
			"opp": display_opp_team.upper(),
			"text": "",
			"rank": "",
			"points": 0.0,
			"players": "",
			"stats": None
		}
		total_stats = {}
		player_txt = []
		for player in players_arr:
			if player not in team_stats or "wk{}".format(week) not in team_stats[player]:
				continue
			elif pos not in ["K", "DEF"] and ("snap_counts" not in team_stats[player]["wk{}".format(week)] or not team_stats[player]["wk{}".format(week)]["snap_counts"]):
				# don't add if player got 0 snaps / messes up percs
				continue

			week_stats = team_stats[player]["wk{}".format(week)]
			
			for s in week_stats:
				#print(player, s, week)
				if s not in total_stats:
					total_stats[s] = [] if s == "fg_made" else 0

				if s == "fg_made":
					total_stats[s].extend(week_stats[s])
				else:
					total_stats[s] += week_stats[s]
			if player == "OFF":
				real_pts = calculate_defense_points(week_stats, settings)
			else:
				real_pts = get_points_from_settings(week_stats, settings)
			player_txt.append("wk{} {}: {} {} pts ({})".format(idx, opp_team, player, real_pts, get_pretty_stats(week_stats, pos, settings)))
			if "points" not in total_stats:
				total_stats["points"] = 0
			total_stats["points"] += real_pts
		try:
			j["team"] = team
			j["opp_team"] = opp_team
			j["stats"] = total_stats 
			j["text"] = get_pretty_stats(total_stats, pos, settings)
			if player == "OFF":
				real_pts = calculate_defense_points(total_stats, settings)
			else:
				real_pts = get_points_from_settings(total_stats, settings)
			j["points"] = round(real_pts, 2)
			j["players"] = player_txt

			# TOT
			tot_stats["points"] += j["points"]
			for key in total_stats:
				if key not in tot_stats["stats"]:
					tot_stats["stats"][key] = 0
				tot_stats["stats"][key] += total_stats[key]
		except:
			pass

		opp_stats.append(j)
	tot_stats["text"] = get_pretty_stats(tot_stats["stats"], pos, settings)
	tot_stats["rank"] = "{} points allowed <span>{}{} highest</span>".format(
		round(tot_stats["points"], 2),
		0,0)
	#   ranks[opp_team][pos.upper()]["tot"],
	#   get_suffix(ranks[opp_team][pos.upper()]["tot"])
	#)
	return opp_stats, tot_stats

def get_total_ranks(curr_week, settings):
	ranks, defense_tot = get_ranks(curr_week, settings)

	print("RANK|QB|RB|WR|TE|K|DEF")
	print(":--|:--|:--|:--|:--|:--|:--")
	for idx in range(1, 33):
		s = "**{}**".format(idx)
		for pos in ["QB", "RB", "WR", "TE", "K", "DEF"]:
			sorted_ranks = sorted(defense_tot, key=operator.itemgetter("{}_ppg".format(pos)), reverse=True)
			display_team = sorted_ranks[idx - 1]["team"]
			if display_team in team_trans:
				display_team = team_trans[display_team]
			tot = round(sorted_ranks[idx - 1]["{}_tot".format(pos)], 2)
			s += "|{} {}".format(display_team, sorted_ranks[idx - 1]["{}_ppg".format(pos)])
		print(s)

def write_team_links():
	url = "https://www.pro-football-reference.com/teams/"
	soup = BS(urllib.urlopen(url).read(), "lxml")
	rows = soup.find("table", id="teams_active").find_all("tr")[2:]
	j = {}
	for tr in rows:
		try:
			link = tr.find("th").find("a").get("href")
			j[link] = 1
		except:
			pass
	with open("{}static/profootballreference/teams.json".format(prefix), "w") as fh:
		json.dump(j, fh, indent=4)

def write_boxscore_links():
	teamlinks = {}
	with open("{}static/profootballreference/teams.json".format(prefix)) as fh:
		teamlinks = json.loads(fh.read())

	for team in teamlinks:
		path = "{}static/profootballreference/{}".format(prefix, team.split("/")[-2])
		if not os.path.exists(path):
			call(["mkdir", "-p", path])
		url = "https://www.pro-football-reference.com{}/2020/gamelog".format(team)
		soup = BS(urllib.urlopen(url).read(), "lxml")
		boxscore_links = {}
		for i in range(16):
			row = soup.find("tr", id="gamelog2020.{}".format(i + 1))
			if row:
				link = row.find("a")
				if link.text == "preview":
					break
				boxscore_links[link.get("href")] = i + 1
		with open("{}/boxscores.json".format(path), "w") as fh:
			json.dump(boxscore_links, fh, indent=4)

def fix_roster(roster, team):
	if team == "atl":
		roster["elliott fry"] = "K"
	elif team == "gnb":
		roster["mason crosby"] = "K"
	elif team == "jax":
		roster["aldrick rosas"] = "K"
		roster["josh lambo"] = "K"
		roster["stephen hauschka"] = "K"
		roster["jonathan brown"] = "K"
	elif team == "nyj":
		roster["chris hogan"] = "WR"
		roster["sergio castillo"] = "K"
	elif team == "phi":
		roster["jake elliott"] = "K"
	elif team == "pit":
		roster["benny snell jr"] = "RB"
	elif team == "ram":
		roster["sam sloman"] = "K"
	elif team == "was":
		roster["jd mckissic"] = "RB"
		roster["antonio gibson"] = "RB"
		roster["logan thomas"] = "TE"
	return

def write_team_rosters(teamlinks={}):
	if not teamlinks:
		with open("{}static/profootballreference/teams.json".format(prefix)) as fh:
			teamlinks = json.loads(fh.read())

	for team in teamlinks:
		roster = {}
		path = "{}static/profootballreference/{}".format(prefix, team.split("/")[-2])

		if not os.path.exists(path):
			os.mkdir(path)
		url = f"https://www.pro-football-reference.com{team}/2020_roster.htm"
		outfile = "{}/roster.html".format(path)
		call(["curl", "-k", url, "-o", outfile])

		# for some reason, the real HTML is commented out?
		soup = BS(open(outfile, 'rb').read(), "lxml")
		starters = soup.find("table", id="starters")
		if starters:
			rows = starters.find_all("tr")[1:]
			for tr in rows:
				tds = tr.find_all("td")
				name = tds[0].text.lower().replace("'", "").replace(".", "")
				pos = tr.find("th").text
				if name.find("starters") == -1:
					roster[name] = pos

		soup = BS(open(outfile, 'rb').read(), "lxml")
		if soup.find("div", id="all_games_played_team") is None:
			continue
		children = soup.find("div", id="all_games_played_team").children
		html = None
		for c in children:
			if isinstance(c, Comment):
				html = c
		os.remove(outfile)

		soup = BS(html, "lxml")
		rows = soup.find("table", id="games_played_team").find_all("tr")[1:]
		for tr in rows:
			tds = tr.find_all("td")
			name = tds[0].text.strip().lower().replace("'", "").replace(".", "")
			pos = tds[2].text
			if name in roster and roster[name] != pos:
				print(name, roster[name], pos)
			roster[name] = pos
		fix_roster(roster, team.split("/")[-2])
		with open("{}/roster.json".format(path), "w") as fh:
			json.dump(roster, fh, indent=4)
	call(["rm", "-rf", "{}static/profootballreference/teams".format(prefix)])
	return

def get_indexes(header_row):
	indexes = {}
	for idx, th in enumerate(header_row):
		# get indexes
		indexes[th.get("data-stat")] = idx
	return indexes

def write_schedule():
	url = "https://www.pro-football-reference.com/years/2020/games.htm"
	soup = BS(urllib.urlopen(url).read(), "lxml")
	rows = soup.find("table", id="games").find_all("tr")[1:] # skip header row
	schedule = {}
	for tr in rows:
		if tr.get("class") and "thead" in tr.get("class"):
			continue
		week = int(tr.find("th").text)
		if week not in schedule:
			schedule[week] = []
		winner = tr.find_all("td")[3].find("a").get("href").split("/")[-2]
		location = tr.find_all("td")[4].text
		loser = tr.find_all("td")[5].find("a").get("href").split("/")[-2]
		s = "{} @ {}".format(loser, winner)
		if location == "@":
			s = "{} @ {}".format(winner, loser)
		schedule[week].append(s)
	with open("{}static/profootballreference/schedule.json".format(prefix), "w") as fh:
		json.dump(schedule, fh, indent=4)

short_names = {"falcons": "atl", "bills": "buf", "panthers": "car", "bears": "chi", "bengals": "cin", "browns": "cle", "colts": "clt", "cardinals": "crd", "cowboys": "dal", "broncos": "den", "lions": "det", "packers": "gnb", "texans": "htx", "jaguars": "jax", "chiefs": "kan", "dolphins": "mia", "vikings": "min", "saints": "nor", "patriots": "nwe", "giants": "nyg", "jets": "nyj", "titans": "oti", "eagles": "phi", "steelers": "pit", "raiders": "rai", "rams": "ram", "ravens": "rav", "chargers": "sdg", "seahawks": "sea", "49ers": "sfo", "buccaneers": "tam", "washington": "was"}

def get_kicking_stats(outfile):
	soup = BS(open(outfile, 'rb').read(), "lxml")
	rows = soup.find("table", id="scoring").find_all("tr")
	stats = {}
	for row in rows[1:]:
		tds = row.find_all("td")
		team = short_names[tds[1].text.lower()]
		detail = tds[2]
		m = re.search(r"(\d+) yard field goal", detail.text)
		if m:
			name = detail.find("a").text.strip().lower().replace(".", "").replace("'", "")
			if name not in stats:
				stats[name] = []
			distance = m.group(1)
			stats[name].append(distance)
	return stats

def get_defense_stats_from_scoring(outfile, team):
	soup = BS(open(outfile, 'rb').read(), "lxml")
	rows = soup.find("table", id="scoring").find_all("tr")
	vis_score = 0
	home_score = 0
	conversions = 0
	safety = 0
	def_tds = 0
	for row in rows[1:]:
		tds = row.find_all("td")
		ck_team = short_names[tds[1].text.lower()]        
		if ck_team == team:
			if int(tds[-2].text) - vis_score == 8:
				conversions += 1
			elif int(tds[-1].text) - home_score == 8:
				conversions += 1
		else:
			if tds[2].text.find("Safety") >= 0:
				safety += 1
			elif tds[2].text.find("interception return") >= 0 or tds[2].text.find("fumble return") >= 0:
				def_tds += 1
		vis_score = int(tds[-2].text)
		home_score = int(tds[-1].text)
	return {"2pt_conversions": conversions, "safety": safety, "def_tds": def_tds}

def add_defense_stats(stats, tds):
	for td in tds:
		key = td.get("data-stat")
		if key not in ["pass_int", "pass_sacked", "pass_td", "rush_td", "fumbles_lost", "fgm", "xpm", "punt_ret_td", "kick_ret_td"]:
			continue
		
		if not td.text:
			val = 0
		else:
			val = int(td.text)
		if key not in stats["OFF"]:
			stats["OFF"][key] = 0
		stats["OFF"][key] += val
	return

def add_stats(boxscorelinks, team, teampath, boxlink, week_arg, team_arg):
	url = "https://www.pro-football-reference.com{}#all_team_stats".format(boxlink)

	home_team = re.match(r".*\d+(.*).htm", boxlink).group(1)
	away_team = None
	if home_team != team:
		away_team = team

	if week_arg and boxscorelinks[boxlink] != week_arg:
		return
	elif team_arg and team != team_arg:
		return

	outfile = "{}/wk{}.html".format(teampath, boxscorelinks[boxlink])
	if os.path.exists(outfile):
		from datetime import datetime
		last_modified = os.stat(outfile).st_mtime
		dt = datetime.fromtimestamp(last_modified)

	call(["curl", "-k", url, "-o", outfile])
	
	kicking_stats = get_kicking_stats(outfile)
	def_stats = get_defense_stats_from_scoring(outfile, team)
	stats = {"OFF": def_stats}
	outer_ids = ["all_player_offense", "all_kicking", "all_returns", "all_home_snap_counts", "all_vis_snap_counts"]
	inner_ids = ["player_offense", "kicking", "returns", "home_snap_counts", "vis_snap_counts"]
	player_teams = {}

	for i in range(len(outer_ids)):
		soup = BS(open(outfile, 'rb').read(), "lxml")
		children = soup.find("div", id=outer_ids[i]).children
		if soup.find("table", id=inner_ids[i]) is None:
			html = None
			for c in children:
				if isinstance(c, Comment):
					soup = BS(c, "lxml")
					break

		#print(i, html is None, outfile)
		rows = soup.find("table", id=inner_ids[i]).find_all("tr")
		for tr in rows[2:]:
			classes = tr.get("class")
			if classes and "thead" in classes:
				continue
			name = tr.find("th").text.strip().lower().replace("'", "").replace(".", "")
			data = tr.find_all("td")
			if "snap" not in inner_ids[i]:
				ck_team = get_abbr(data[0].text.lower()) # might have different abbr
				if away_team is None and ck_team != home_team:
					away_team = ck_team
			
			if "snap" in inner_ids[i]:
				# if player got 0 points but had snaps
				if data[0].text not in ["QB", "RB", "WR", "TE", "K"]:
					continue
				if name not in stats:
					if inner_ids[i].startswith("home") and home_team == team:
						stats[name] = {}
					elif inner_ids[i].startswith("vis") and away_team == team:
						stats[name] = {}
				try:
					stats[name]["snap_counts"] = int(data[1].text)
					stats[name]["snap_perc"] = int(data[2].text.replace("%", ""))
				except:
					pass
			elif outer_ids[i] == "all_returns":
				# add kick_ret , punt_ret for other team
				if team != ck_team:
					add_defense_stats(stats, data[1:])
			elif team == ck_team:
				if name not in stats:
					stats[name] = {}
				add_defense_stats(stats, data[1:])
				if inner_ids[i] == "kicking":
					try:
						stats[name]["fg_made"] = kicking_stats[name]
					except:
						pass
				for td in data[1:]: # skip team
					try:                        
						if td.get("data-stat") == "pass_rating":
							stats[name][td.get("data-stat")] = float(td.text)
						else:   
							stats[name][td.get("data-stat")] = int(td.text)
					except:
						stats[name][td.get("data-stat")] = 0
	for s in ["kick_ret_td", "punt_ret_td"]:
		if s not in stats["OFF"]:
			stats["OFF"][s] = 0
	with open("{}/wk{}.json".format(teampath, boxscorelinks[boxlink]), "w") as fh:
		json.dump(stats, fh, indent=4)
	os.remove(outfile)

def write_boxscore_stats(week_arg, team_arg):
	teamlinks = {}
	with open("{}static/profootballreference/teams.json".format(prefix)) as fh:
		teamlinks = json.loads(fh.read())

	for link in teamlinks:
		team = link.split("/")[-2]
		teampath = "{}static/profootballreference/{}".format(prefix, team)
		boxscorelinks = {}
		with open("{}/boxscores.json".format(teampath)) as fh:
			boxscorelinks = json.loads(fh.read())
		for boxlink in boxscorelinks:
			#print(team, boxlink)
			add_stats(boxscorelinks, team, teampath, boxlink, week_arg, team_arg)


if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("-c", "--cron", action="store_true", help="Start Cron Job")
	parser.add_argument("-r", "--ranks", action="store_true", help="Get Ranks")    
	parser.add_argument("-schedule", "--schedule", help="Print Schedule", action="store_true")
	parser.add_argument("-s", "--start", help="Start Week", type=int)
	parser.add_argument("-e", "--end", help="End Week", type=int)
	parser.add_argument("-t", "--team", help="Get Team")
	parser.add_argument("-p", "--pos", help="Get Pos")
	parser.add_argument("-w", "--week", help="Week", type=int)

	args = parser.parse_args()
	curr_week = 3

	if args.start:
		curr_week = args.start
	settings = {'0_points_allowed': 10, '7-13_points_allowed': 4, 'sack': 1, 'ppr': 0.5, 'touchdown': 6, 'pass_tds': 4, 'fumble_recovery': 2, '1-6_points_allowed': 7, 'xpm': 1, 'fumbles_lost': -2, 'rec_tds': 6, 'interception': 2, 'field_goal_0-19': 3, 'safety': 2, 'field_goal_50+': 5, 'pass_yds': 25, 'field_goal_20-29': 3, 'pass_int': -2, 'rush_yds': 10, 'rush_tds': 6, '21-27_points_allowed': 0, '28-34_points_allowed': -1, '14-20_points_allowed': 1, 'field_goal_30-39': 3, 'field_goal_40-49': 4, '35+_points_allowed': -4, 'rec_yds': 10}

	if args.schedule:
		schedule = read_schedule()
		print(schedule[str(curr_week)])
	elif args.ranks:
		get_total_ranks(curr_week, settings)
	elif args.team and args.pos:
		ranks = get_ranks(curr_week, settings)
		opp, tot = position_vs_opponent_stats(args.team, args.pos, ranks, settings)
		teamname = team_trans[args.team] if args.team in team_trans else args.team
		print("**{} vs. {}**".format(teamname.upper(), args.pos))
		for idx, data in enumerate(opp):
			if idx + 1 > curr_week:
				continue
			print("\n#Wk{} vs. {} {} - {} pts".format(data["week"], data["opp"], args.pos, data["points"]))
			arr = [ d.split(": ")[1] for d in data["players"] ]
			print("\n".join(arr))
		#print(opp1)
	elif args.cron:
		pass
		# only needs to be run once in a while
		
		#write_team_links()
		#write_schedule()
		
		#write_team_rosters()
		#write_boxscore_links()
		#write_boxscore_stats(args.week, args.team)
		#calculate_aggregate_stats()

	#write_team_rosters()
	#write_boxscore_stats()
	#calculate_aggregate_stats()
	#get_opponents("ari")
