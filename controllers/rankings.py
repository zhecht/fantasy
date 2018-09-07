from flask import *
import operator
import sys
from controllers.espn_stats import *
from controllers.stats import *
from controllers.fantasypros_stats import *
from controllers.read_rosters import *


rankings = Blueprint('rankings', __name__, template_folder='views')

def merge_two_dicts(x, y):
	z = x.copy()
	z.update(y)
	return z

@rankings.route('/rankings')
def rankings_route():
	try:
		curr_week = int(request.args.get("week"))
	except:
		curr_week = 1

	players_on_teams, name_translations = read_rosters()
	players_on_FA = read_FA()
	players_on_teams = merge_two_dicts(players_on_teams, players_on_FA)

	yahoo_rankings_json = read_yahoo_rankings(curr_week, players_on_teams)
	espn_rankings_json = read_espn_rankings(curr_week, players_on_teams)
	fantasypros_rankings_json = read_fantasypros_rankings(curr_week, curr_week + 1)
	actual_json = read_actual_rankings(curr_week, curr_week + 1)

	player_rankings = []
	for position in ["qb", "rb", "wr", "te"]:
		for player in actual_json[position]:
			espn_rank = espn_rankings_json[position][player]
			yahoo_rank = yahoo_rankings_json[position][player]
			fantasypros_rank = fantasypros_rankings_json[position][player]
			actual_rank = actual_json[position][player]

			if player not in players_on_teams:
				continue
			player_rankings.append({"name": player, "espn": espn_rank, "yahoo": yahoo_rank, "fantasypros": fantasypros_rank, "actual": actual_rank})

	graphs = []
	# Graph: Player x % ERR
	
	yahoo_rankings_sorted = sorted(player_rankings, key=operator.itemgetter("yahoo"))
	espn_rankings_sorted = sorted(player_rankings, key=operator.itemgetter("espn"))
	fantasypros_rankings_sorted = sorted(player_rankings, key=operator.itemgetter("fantasypros"))
	actual_rankings_sorted = sorted(player_rankings, key=operator.itemgetter("actual"))
	
	for position in ["qb", "rb", "wr", "te"]:
		graph = {"title": "Projected Vs. Actual Rank [{}]".format(position), "position": position, "actual": [], "espn": [], "yahoo": [], "fantasypros": [], "name": []}

		graph["name"] = [player["name"] for player in actual_json[position]]
		for player in actual_json[position]:
			graph["actual"].append(actual_json[position][player])
			graph["espn"].append(espn_rankings_json[position][player])
			graph["yahoo"].append(yahoo_rankings_json[position][player])
			graph["fantasypros"].append(fantasypros_rankings_json[position][player])

		total_players = len(graph["name"])
		for key in ["name", "actual", "espn", "yahoo", "fantasypros"]:
			graph[key] = ','.join(graph[key])
		graphs.append(graph)


	return render_template("rankings.html", graphs=graphs)


