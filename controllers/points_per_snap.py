import operator
import sys

try:
	import controllers.read_rosters as read_rosters
	import controllers.stats as stats
	import controllers.snap_stats as snap_stats
except:
	import read_rosters
	import stats
	import snap_stats

def merge_two_dicts(x, y):
	z = x.copy()
	z.update(y)
	return z

curr_week = 3
players_on_teams, name_translations = read_rosters.read_rosters()
players_on_FA = read_rosters.read_FA()
players_on_teams = merge_two_dicts(players_on_teams, players_on_FA)
snap_stats_json = snap_stats.read_snap_stats()

player_stats = {}

for week in range(1, curr_week):
	actual_json = stats.read_actual_stats(week, week + 1)

	for player in players_on_teams:
		if player not in player_stats:
			player_stats[player] = {"total_snaps": 0, "total_points": 0.0, "team_total_snaps": 0}
		try:
			player_snaps = int(snap_stats_json[player]["counts"].split(",")[week - 1])
			player_perc = int(snap_stats_json[player]["perc"].split(",")[week - 1])
			player_stats[player]["total_snaps"] += player_snaps
			player_stats[player]["team_total_snaps"] += (player_snaps / float(player_perc / 100.0))
			player_stats[player]["total_points"] += float(actual_json[player])
		except:
			continue

player_arr = []
for player in player_stats:
	try:
		player_arr.append({"name": player, "total_points": player_stats[player]["total_points"], "total_snaps": player_stats[player]["total_snaps"], "team_total_snaps": player_stats[player]["team_total_snaps"], "points_per_snap": player_stats[player]["total_points"] / float(player_stats[player]["total_snaps"])})
	except:
		continue

player_sorted = sorted(player_arr, key=operator.itemgetter("points_per_snap"), reverse=True)

print("Player|Total Points|Total Snaps|Points Per Snap")
print(":--|:--|:--|:--")
for player_hash in player_sorted:
	if player_hash["total_snaps"] / player_hash["team_total_snaps"] > .4:
		print("{}|{}|{}|{}".format(player_hash["name"].title(), player_hash["total_points"], player_hash["total_snaps"], round(player_hash["points_per_snap"], 2)))
		pass


