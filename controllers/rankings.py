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
	yahoo_json = read_yahoo_stats(curr_week, curr_week + 1)

	player_rankings = []
	for position in ["qb", "rb", "wr", "te"]:
		cutoff = 30 if position == "qb" else 40
		for player in actual_json[position]:
			if player not in players_on_teams:
				continue
			try:
				espn_rank = espn_rankings_json[position][player]
				yahoo_rank = yahoo_rankings_json[position][player]
				fantasypros_rank = fantasypros_rankings_json[position][player]
				actual_rank = actual_json[position][player]
			except:
				continue

			
			player_rankings.append({"name": player, "espn": espn_rank, "yahoo": yahoo_rank, "fantasypros": fantasypros_rank, "actual": actual_rank, "position": position})

	graphs = []
	# Graph: Player x % ERR
	
	yahoo_rankings_sorted = sorted(player_rankings, key=operator.itemgetter("yahoo"))
	espn_rankings_sorted = sorted(player_rankings, key=operator.itemgetter("espn"))
	fantasypros_rankings_sorted = sorted(player_rankings, key=operator.itemgetter("fantasypros"))
	actual_rankings_sorted = sorted(player_rankings, key=operator.itemgetter("actual"))
	
	for position in ["qb", "rb", "wr", "te"]:
		graph = {"title": "Wk{} Projected Vs. Actual Rank [{}]".format(curr_week, position), "position": position, "actual": [], "espn": [], "yahoo": [], "fantasypros": [], "name": []}

		for player in actual_rankings_sorted:
			try:
				if player["position"] == position:
					graph["name"].append(" ".join(player["name"].split(" ")[1:]))
					graph["actual"].append(str(actual_json[position][player["name"]]))
					graph["espn"].append(str(espn_rankings_json[position][player["name"]]))
					graph["yahoo"].append(str(yahoo_rankings_json[position][player["name"]]))
					graph["fantasypros"].append(str(fantasypros_rankings_json[position][player["name"]]))
			except:
				continue

		total_players = len(graph["name"])
		for key in ["name", "actual", "espn", "yahoo", "fantasypros"]:
			graph[key] = ','.join(graph[key])
		graphs.append(graph)

	error_graphs = []
	for position in ["qb", "rb", "te", "wr"]:
		total_err = 0
		total_abs_err = 0
		for site in ["yahoo", "espn", "fantasypros"]:
			graph = {"title": "Wk{} {} % Err Vs. Projected Rank [{}]".format(curr_week, site, position), "position": position, "site": site, "actual": [], "projected": [], "err": [], "abs_err": [], "name": []}

			arr = yahoo_rankings_sorted
			if site == "espn":
				arr = espn_rankings_sorted
			elif site == "fantasypros":
				arr = fantasypros_rankings_sorted

			for player in arr:
				try:
					if player["position"] == position:
						graph["name"].append(" ".join(player["name"].split(" ")[1:]))
						
						actual = actual_json[position][player["name"]]
						proj_rank = yahoo_rankings_json[position][player["name"]]
						if site == "espn":
							proj_rank = espn_rankings_json[position][player["name"]]
						elif site == "fantasypros":
							proj_rank = fantasypros_rankings_json[position][player["name"]]

						graph["actual"].append(str(actual))
						graph["projected"].append(str(proj_rank))

						#err = (proj_rank - actual) / proj_rank
						
						err = proj_rank - actual
						perc_err = round(err * 100, 2)
						graph["err"].append(str(round(err, 2)))
						graph["abs_err"].append(str(perc_err))
						total_err += err
						total_abs_err += abs(err)
				except:
					continue
			
			cutoff = 30 if position == "qb" else 50
			#for key in ["actual", "projected", "err", "perc_err", "name"]:
			#	graph[key] = graph[key][:cutoff]

			total_players = len(graph["name"])
			avg_err = total_err / float(total_players)
			avg_abs_err = total_abs_err / float(total_players)

			best_avg = 100
			best_5_range = [0,0]
			for first in range(total_players):
				avg = 0
				total_len = 5
				for idx in range(first, first + 5):
					try:
						avg += float(graph["err"][idx])
					except:
						total_len -= 1
						continue
				avg = avg / total_len
				if avg < best_avg:
					best_avg = avg
					best_5_range = [first, first + total_len]
			# find best avg_err in range of 10
			best_avg = 100
			best_10_range = [0,0]
			for first in range(total_players):
				avg = 0
				total_len = 10
				for idx in range(first, first + 10):
					try:
						avg += float(graph["err"][idx])
					except:
						total_len -= 1
						continue
				avg = avg / total_len
				if avg < best_avg:
					best_avg = avg
					best_10_range = [first, first + total_len]

			for key in ["actual", "projected", "err", "name"]:
				graph[key] = ','.join(graph[key])

			graph["avg_err"] = avg_err
			graph["avg_abs_err"] = avg_abs_err
			graph["best_10_avg_range"] = "{}{} - {}{}".format(position,best_10_range[0],position,best_10_range[1])
			graph["best_5_avg_range"] = "{}{} - {}{}".format(position,best_5_range[0],position,best_5_range[1])
			error_graphs.append(graph)
	return render_template("rankings.html", graphs=graphs,error_graphs=error_graphs, curr_week=curr_week)


