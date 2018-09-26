from flask import *
import operator
import sys
from controllers.espn_stats import *
from controllers.stats import *
from controllers.fantasypros_stats import *
from controllers.read_rosters import *
from controllers.borischen import *


rankings = Blueprint('rankings', __name__, template_folder='views')

def merge_two_dicts(x, y):
	z = x.copy()
	z.update(y)
	return z

@rankings.route('/rankings')
def rankings_route():
	real_week = 5

	try:
		arg_week = int(request.args.get("week"))
		cutoff = arg_week + 1
		is_all_weeks = False
	except:
		arg_week = 1
		cutoff = real_week
		is_all_weeks = True

	arg_pos = request.args.get("pos")
	if arg_pos is None:
		arg_pos = "QB"

	if arg_week >= real_week:
		arg_week = 1
		cutoff = 2

	players_on_teams, name_translations = read_rosters()
	players_on_FA = read_FA()
	players_on_teams = merge_two_dicts(players_on_teams, players_on_FA)
	graphs = []
	error_graphs = []


	for curr_week in range(arg_week, cutoff):
		yahoo_rankings_json = read_yahoo_rankings(curr_week, players_on_teams)

		espn_rankings_json = read_espn_rankings(curr_week, players_on_teams)
		fantasypros_rankings_json = read_fantasypros_rankings(curr_week, curr_week + 1)
		borischen_rankings_json = read_borischen_rankings(curr_week)
		actual_json = read_actual_rankings(curr_week, curr_week + 1)
		yahoo_json = read_yahoo_stats(curr_week, curr_week + 1)

		player_rankings = []
		for position in ["qb", "rb", "wr", "te"]:
			#cutoff = 30 if position == "qb" else 40
			for player in actual_json[position]:
				if player not in players_on_teams:
					continue
				try:
					espn_rank = espn_rankings_json[position][player]
					yahoo_rank = yahoo_rankings_json[position][player]
					fantasypros_rank = fantasypros_rankings_json[position][player]
					borischen_rank = borischen_rankings_json[position][player]
					actual_rank = actual_json[position][player]
				except:
					#print(player)
					continue

				
				player_rankings.append({"name": player, "espn": espn_rank, "yahoo": yahoo_rank, "fantasypros": fantasypros_rank, "borischen": borischen_rank, "actual": actual_rank, "position": position})

		
		# 
		
		yahoo_rankings_sorted = sorted(player_rankings, key=operator.itemgetter("yahoo"))
		espn_rankings_sorted = sorted(player_rankings, key=operator.itemgetter("espn"))
		fantasypros_rankings_sorted = sorted(player_rankings, key=operator.itemgetter("fantasypros"))
		borischen_rankings_sorted = sorted(player_rankings, key=operator.itemgetter("borischen"))
		actual_rankings_sorted = sorted(player_rankings, key=operator.itemgetter("actual"))
		
		for position in ["qb", "rb", "te", "wr"]:
			
			for site in ["yahoo", "espn", "fantasypros", "borischen"]:
				total_err = 0
				total_abs_err = 0
				total_abs_err_perc = 0
				total_abs_err_range = {"1_10": 0, "31_40": 0, "11_20": 0, "21_30": 0}
				graph = {"week": curr_week, "title": "Wk{} {} % Err Vs. Projected Rank [{}]".format(curr_week, site, position), "position": position, "site": site, "actual": [], "projected": [], "err": [], "abs_err": [], "abs_perc_err": [], "full_name": [], "name": [], "exact": 0, "within_2": 0, "within_5": 0, "within_10": 0}

				arr = yahoo_rankings_sorted
				if site == "espn":
					arr = espn_rankings_sorted
				elif site == "fantasypros":
					arr = fantasypros_rankings_sorted
				elif site == "borischen":
					arr = borischen_rankings_sorted

				
				for player in arr:
					try:
						if player["position"] == position:
							graph["name"].append(" ".join(player["name"].split(" ")[1:]))
							graph["full_name"].append(player["name"])
							
							actual = actual_json[position][player["name"]]
							proj_rank = yahoo_rankings_json[position][player["name"]]
							if site == "espn":
								proj_rank = espn_rankings_json[position][player["name"]]
							elif site == "fantasypros":
								proj_rank = fantasypros_rankings_json[position][player["name"]]
							elif site == "borischen":
								proj_rank = borischen_rankings_json[position][player["name"]]

							graph["actual"].append(str(actual))
							graph["projected"].append(str(proj_rank))
							
							err = proj_rank - actual
							
							if abs(err) <= 10:
								graph["within_10"] += 1
								if abs(err) <= 5:
									graph["within_5"] += 1
									if abs(err) <= 2:
										graph["within_2"] += 1
										if err == 0:
											graph["exact"] += 1

							perc_err = round(err * 100, 2)
							graph["err"].append(str(round(err, 2)))
							graph["abs_err"].append(str(perc_err))
							graph["abs_perc_err"].append(err / proj_rank)
							total_err += err
							total_abs_err += abs(err)
							total_abs_err_perc += abs(err / proj_rank)

							for _range in total_abs_err_range:
								start, end = _range.split("_")
								if proj_rank >= int(start) and proj_rank <= int(end):
									total_abs_err_range[_range] += abs(err)
					except:
						continue
				
				cutoff = 30 if (position == "qb" or position == "te") else 40
				for key in ["actual", "projected", "err", "abs_err", "name", "full_name"]:
					graph[key] = graph[key][:cutoff]

				total_players = len(graph["name"])

				graph["exact"] = round((graph["exact"] / float(total_players) * 100), 2)
				graph["within_2"] = round((graph["within_2"] / float(total_players) * 100), 2)
				graph["within_5"] = round((graph["within_5"] / float(total_players) * 100), 2)
				graph["within_10"] = round((graph["within_10"] / float(total_players) * 100), 2)
				avg_err = total_err / float(total_players)
				avg_abs_err = round(total_abs_err / float(total_players), 2)
				avg_abs_err_perc = round(total_abs_err_perc / float(total_players), 2)

				"""
				best_range = [[0,0], [0,0]]
				for main_idx, _range in enumerate([5, 10]):
					best_avg = 100
					for first in range(total_players):
						avg = 0
						total_len = _range
						for idx in range(first, first + 5):
							try:
								avg += float(graph["err"][idx])
							except:
								total_len -= 1
								continue
						avg = avg / total_len
						if avg < best_avg:
							best_avg = avg
							best_range[main_idx][0] = first
							best_range[main_idx][1] = first + total_len
				"""

				for key in ["actual", "projected", "err", "name", "full_name"]:
					graph[key] = ','.join(graph[key])

				for _range in total_abs_err_range:
					start, end = map(int, _range.split("_"))
					graph["avg_abs_err_"+_range] = round(total_abs_err_range[_range] / (end - start + 1.0) / 1.0, 2)

				graph["avg_err"] = avg_err
				graph["avg_abs_err"] = avg_abs_err
				graph["avg_abs_err_perc"] = avg_abs_err_perc
				#graph["best_5_avg_range"] = "{}{} - {}{}".format(position.upper(),best_range[0][0] + 1,position.upper(),best_range[0][1] + 1)
				#graph["best_10_avg_range"] = "{}{} - {}{}".format(position.upper(),best_range[1][0] + 1,position.upper(),best_range[1][1] + 1)
				
				error_graphs.append(graph)

	player_accuracy_dict = {}
	for graph in error_graphs:
		names = graph["full_name"].split(",")

		for idx, name in enumerate(names):
			if name not in player_accuracy_dict:
				player_accuracy_dict[name] = {"yahoo_projected_ranks": [], "espn_projected_ranks": [], "borischen_projected_ranks": [], "fantasypros_projected_ranks": [], "actual_ranks": []}

			player_accuracy_dict[name][graph["site"]+"_projected_ranks"].append(graph["projected"].split(",")[idx])
			if graph["site"] == "yahoo":
				# Only add actual once per site
				player_accuracy_dict[name]["actual_ranks"].append(graph["actual"].split(",")[idx])

	player_accuracy = []
	for player in player_accuracy_dict:
		site_avg_abs_err = [0,0,0,0]
		for idx, site in enumerate(["yahoo", "espn", "fantasypros", "borischen"]):
			avg_abs_err = 0
			for proj_rank, act_rank in zip(player_accuracy_dict[player][site+"_projected_ranks"], player_accuracy_dict[player]["actual_ranks"]):
				avg_abs_err += abs(float(proj_rank) - float(act_rank))
			site_avg_abs_err[idx] = avg_abs_err

		if len(player_accuracy_dict[player]["yahoo_projected_ranks"]) == real_week - 1 and len(player_accuracy_dict[player]["espn_projected_ranks"]) == real_week - 1 and len(player_accuracy_dict[player]["fantasypros_projected_ranks"]) == real_week - 1 and len(player_accuracy_dict[player]["borischen_projected_ranks"]) == real_week - 1:
			data = {"name": player, "avg_abs_err": 0}
			for idx, site in enumerate(["yahoo", "espn", "fantasypros", "borischen"]):
				data[site+"_avg_abs_err"] = round(site_avg_abs_err[idx] / float(len(player_accuracy_dict[player]["actual_ranks"])), 2)
				data["avg_abs_err"] += site_avg_abs_err[idx] / float(len(player_accuracy_dict[player]["actual_ranks"]))
			player_accuracy.append(data)

		#if len(player_accuracy_dict[player]["actual_ranks"]) == real_week - 1:
			#player_accuracy.append({"name": player, "yahoo_avg_abs_err": yahoo_avg_abs_err / float(len(player_accuracy_dict[player]["actual_ranks"])), "espn_avg_abs_err": espn_avg_abs_err / float(len(player_accuracy_dict[player]["actual_ranks"])), "fantasypros_avg_abs_err": fantasypros_avg_abs_err / float(len(player_accuracy_dict[player]["actual_ranks"])), "borischen_avg_abs_err": borischen_avg_abs_err / float(len(player_accuracy_dict[player]["actual_ranks"]))})

	overall_player_accuracy = sorted(player_accuracy, key=operator.itemgetter("avg_abs_err"))

	print("#Average Rank Error")
	print("Player|Avg Err|Yahoo|ESPN|FantasyPros|Borischen")
	for player in overall_player_accuracy[:40]:
		print("{}|{}|{}|{}|{}|{}".format(player["name"], round(player["avg_abs_err"] / 4.0, 2), player["yahoo_avg_abs_err"], player["espn_avg_abs_err"], player["fantasypros_avg_abs_err"], player["borischen_avg_abs_err"]))
	"""
	yahoo_player_accuracy = sorted(player_accuracy, key=operator.itemgetter("yahoo_avg_abs_err"))
	espn_player_accuracy = sorted(player_accuracy, key=operator.itemgetter("espn_avg_abs_err"))
	fantasypros_player_accuracy = sorted(player_accuracy, key=operator.itemgetter("fantasypros_avg_abs_err"))
	borischen_player_accuracy = sorted(player_accuracy, key=operator.itemgetter("borischen_avg_abs_err"))

	end = 10
	for player in yahoo_player_accuracy[:end]:
		print("YAHOO:", player["name"], player_accuracy_dict[player["name"]]["actual_ranks"])
	for player in espn_player_accuracy[:end]:
		print("ESPN:", player["name"], player_accuracy_dict[player["name"]]["actual_ranks"])
	for player in fantasypros_player_accuracy[:end]:
		print("FantasyPros:", player["name"], player_accuracy_dict[player["name"]]["actual_ranks"])
	for player in borischen_player_accuracy[:end]:
		print("Borischen:", player["name"], player_accuracy_dict[player["name"]]["actual_ranks"])
	"""

	return render_template("rankings.html", real_week=real_week, graphs=graphs,error_graphs=error_graphs, curr_week=arg_week, sites=["yahoo", "espn", "fantasypros", "borischen"], all_weeks=[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17], is_all_weeks=is_all_weeks, pos=arg_pos)


