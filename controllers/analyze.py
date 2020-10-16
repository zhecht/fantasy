
import operator
import os

from profootballreference import *
from snap_stats import *

if __name__ == "__main__":
	curr_week = 5
	schedule = read_schedule()
	snap_stats = read_snap_stats(curr_week)
	over_expected = True
	settings = {'0_points_allowed': 10, '7-13_points_allowed': 4, 'sack': 1, 'ppr': 0.5, 'touchdown': 6, 'pass_tds': 4, 'fumble_recovery': 2, '1-6_points_allowed': 7, 'xpm': 1, 'fumbles_lost': -2, 'rec_tds': 6, 'interception': 2, 'field_goal_0-19': 3, 'safety': 2, 'field_goal_50+': 5, 'pass_yds': 25, 'field_goal_20-29': 3, 'pass_int': -2, 'rush_yds': 10, 'rush_tds': 6, '21-27_points_allowed': 0, '28-34_points_allowed': -1, '14-20_points_allowed': 1, 'field_goal_30-39': 3, 'field_goal_40-49': 4, '35+_points_allowed': -4, 'rec_yds': 10}
	display_team_trans = {"rav": "bal", "htx": "hou", "oti": "ten", "sdg": "lac", "ram": "lar", "clt": "ind", "crd": "ari", "gnb": "gb", "kan": "kc", "nwe": "ne", "rai": "lv", "sfo": "sf", "tam": "tb", "nor": "no"}
	
	cut = 15
	ranks, defense_tot = get_ranks(curr_week, settings, over_expected)
	print(f"#Week {curr_week+1}: Top {cut} players against Defenses that allow the most Fantasy Points vs. Projections")
	for pos in ["QB", "RB", "WR", "TE", "K", "DEF"]:
		print(f"\n#{pos}")
		print(f"Defense|Actual vs. Projected %|Week {curr_week+1} Players")
		print(":--|:--|:--")
		sorted_ranks = sorted(defense_tot, key=operator.itemgetter(f"{pos}_ppg"), reverse=True)
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