
import operator
import os

from profootballreference import *
from snap_stats import *

settings = {'0_points_allowed': 10, '7-13_points_allowed': 4, 'sack': 1, 'ppr': 0.5, 'touchdown': 6, 'pass_tds': 4, 'fumble_recovery': 2, '1-6_points_allowed': 7, 'xpm': 1, 'fumbles_lost': -2, 'rec_tds': 6, 'interception': 2, 'field_goal_0-19': 3, 'safety': 2, 'field_goal_50+': 5, 'pass_yds': 25, 'field_goal_20-29': 3, 'pass_int': -2, 'rush_yds': 10, 'rush_tds': 6, '21-27_points_allowed': 0, '28-34_points_allowed': -1, '14-20_points_allowed': 1, 'field_goal_30-39': 3, 'field_goal_40-49': 4, '35+_points_allowed': -4, 'rec_yds': 10}
display_team_trans = {"rav": "bal", "htx": "hou", "oti": "ten", "sdg": "lac", "ram": "lar", "clt": "ind", "crd": "ari", "gnb": "gb", "kan": "kc", "nwe": "ne", "rai": "lv", "sfo": "sf", "tam": "tb", "nor": "no"}

def loop(curr_week, cut, which):
	ranks, defense_tot = get_ranks(curr_week, settings, over_expected)
	print(f"#Week {curr_week+1}: Top {cut} players against Defenses that allow the most Fantasy Points vs. Projections")
	for pos in ["QB", "RB", "WR", "TE", "K", "DEF"]:
		print(f"\n#{pos}")
		print(f"Defense|Actual vs. Projected %|Week {curr_week+1} Players")
		print(":--|:--|:--")
		reverse = True
		if which == "bottom":
			reverse = False
		sorted_ranks = sorted(defense_tot, key=operator.itemgetter(f"{pos}_ppg"), reverse=reverse)
		for row in sorted_ranks[:cut]:
			team = row["team"]
			opp_team = get_opponents(team)[curr_week]
			if opp_team == "BYE":
				continue
			team_dis = display_team_trans[team] if team in display_team_trans else team
			opp_team_dis = display_team_trans[opp_team] if opp_team in display_team_trans else opp_team
			val = row[f"{pos}_ppg"]
			players = get_players_by_pos_team(opp_team, pos)
			if pos == "DEF":
				new_players = ["-"]
			elif pos == "K":
				new_players = players
			else:
				new_players = []
				for player in players:
					if player in snap_stats:
						for perc in snap_stats[player]["perc"].split(",")[:curr_week]:
							if int(perc) > 20:
								new_players.append(player)
								break
			players = ", ".join([p.title() for p in new_players])
			print(f"{team_dis.upper()}|{val}%|{opp_team_dis.upper()}: {players}")

# week 14, 15, 16
def loop_weeks(curr_week, cut, week_range, which):
	ranks, defense_tot = get_ranks(curr_week, settings, over_expected)
	schedule = read_schedule()
	team_ppg = {}
	for pos in ["QB", "RB", "WR", "TE", "K", "DEF"]:
		for row in defense_tot:
			team = row["team"]
			if team not in team_ppg:
				team_ppg[team] = {}
			team_ppg[team][f"{pos}_act"] = row[f"{pos}_act"]
			team_ppg[team][f"{pos}_proj"] = row[f"{pos}_proj"]
	playoff_ppg = {}
	for team in team_ppg:
		opponents = get_opponents(team)
		playoff_ppg[team] = {}
		for pos in ["QB", "RB", "WR", "TE", "K", "DEF"]:
			playoff_ppg[team][f"{pos}_act"] = 0
			playoff_ppg[team][f"{pos}_proj"] = 0
			opp_str = []
			for week in week_range:
				opp = opponents[week]
				team_dis = display_team_trans[opp] if opp in display_team_trans else opp
				opp_str.append(team_dis)
				if opp == "BYE":
					continue
				playoff_ppg[team][f"{pos}_act"] += team_ppg[opp][f"{pos}_act"]
				playoff_ppg[team][f"{pos}_proj"] += team_ppg[opp][f"{pos}_proj"]
			playoff_ppg[team][f"{pos}_ppg"] = round(((playoff_ppg[team][f"{pos}_act"] / playoff_ppg[team][f"{pos}_proj"]) - 1) * 100, 2)
			playoff_ppg[team]["opp"] = ", ".join(opp_str)
	
	playoff_ppg_arr = []
	for team in playoff_ppg:
		j = {"team": team, "opp": playoff_ppg[team]["opp"]}
		for pos in ["QB", "RB", "WR", "TE", "K", "DEF"]:
			j[f"{pos}_ppg"] = playoff_ppg[team][f"{pos}_ppg"]
		playoff_ppg_arr.append(j)
	
	for pos in ["QB", "RB", "WR", "TE", "K", "DEF"]:
		print(f"\n#{pos}")
		print(f"Team|Week {week_range[0] + 1}-{week_range[-1] + 1}|Actual vs. Projected %|Players")
		print(":--|:--|:--|:--")
		reverse = True
		if which == "bottom":
			reverse = False
		sorted_ranks = sorted(playoff_ppg_arr, key=operator.itemgetter(f"{pos}_ppg"), reverse=reverse)
		for row in sorted_ranks[:cut]:
			team = row["team"]
			#print(pos, team, row["opp"], row[f"{pos}_ppg"])
			players = get_players_by_pos_team(team, pos)
			new_players = []
			if pos == "DEF":
				new_players = ["-"]
			elif pos == "K":
				new_players = players
			else:
				new_players = []
				for player in players:
					if player in snap_stats:
						for perc in snap_stats[player]["perc"].split(",")[:curr_week]:
							if int(perc) > 20:
								new_players.append(player)
								break
			players = ", ".join([p.title() for p in new_players])
			team_dis = display_team_trans[team] if team in display_team_trans else team
			val = row[f"{pos}_ppg"]
			print(f"{team_dis.upper()}|{row['opp'].upper()}|{val}%|{players}")

if __name__ == "__main__":
	curr_week = 7
	schedule = read_schedule()
	snap_stats = read_snap_stats(curr_week)
	over_expected = True
	
	cut = 15
	#loop(curr_week, cut, which="top")
	loop(curr_week, cut, which="bottom")
	#loop_weeks(curr_week, cut, range(curr_week, curr_week + 5), which="top") # next 5
	#loop_weeks(curr_week, cut, range(13, 16), which="top") # playoffs
	