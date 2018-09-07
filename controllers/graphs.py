from flask import *
import operator
import sys
from controllers.espn_stats import *
from controllers.stats import *
from controllers.fantasypros_stats import *
from controllers.read_rosters import *


graphs = Blueprint('graphs', __name__, template_folder='views')

def merge_two_dicts(x, y):
	z = x.copy()
	z.update(y)
	return z

@graphs.route('/graphs')
def graphs_route():
	try:
		curr_week = int(request.args.get("week"))
		pos = request.args.get("pos")
	except:
		curr_week = 1
		pos = "RB"

	players_on_teams, name_translations = read_rosters()
	players_on_FA = read_FA()
	players_on_teams = merge_two_dicts(players_on_teams, players_on_FA)

	espn_proj_json = read_espn_stats(curr_week, curr_week + 1)
	yahoo_proj_json = read_yahoo_stats(curr_week, curr_week + 1)
	fantasypros_proj_json = read_fantasypros_stats(curr_week, curr_week + 1)
	#espn_proj_next_json = read_espn_stats(curr_week + 1, curr_week + 2)
	#yahoo_proj_next_json = read_yahoo_stats(curr_week + 1, curr_week + 2)
	#fantasypros_proj_next_json = read_fantasypros_stats(curr_week + 1, curr_week + 2)

	actual_json = read_actual_stats(curr_week, curr_week + 1)

	proj_error = []
	for player in actual_json:
		try:
			espn_proj = espn_proj_json[player]
			yahoo_proj = yahoo_proj_json[player]
			fantasypros_proj = fantasypros_proj_json[player]
			espn_proj_next = 0 #espn_proj_next_json[player]
			yahoo_proj_next = 0 #yahoo_proj_next_json[player]
			fantasypros_proj_next = 0 #fantasypros_proj_next_json[player]
			actual = 0 if actual_json[player] == "-" else float(actual_json[player])
		except:
			continue

		if actual == 0 or yahoo_proj == 0 or espn_proj == 0 or player not in players_on_teams:# or yahoo_proj < 5:
			continue

		#yahoo_err = ((yahoo_proj - actual) / actual) * 100
		#espn_err = ((espn_proj - actual) / actual) * 100
		yahoo_err = ((yahoo_proj - actual) / yahoo_proj) * 100
		espn_err = ((espn_proj - actual) / espn_proj) * 100
		fantasypros_err = ((fantasypros_proj - actual) / fantasypros_proj) * 100

		if abs(yahoo_err) > 200 or abs(espn_err) > 200 or abs(fantasypros_err) > 200:
			continue
		proj_error.append({"actual":actual,"text": player, "position": players_on_teams[player]["position"], "yahoo": round(yahoo_err, 2), "yahoo_abs": abs(round(yahoo_err, 2)), "espn": round(espn_err, 2), "espn_abs": abs(round(espn_err, 2)), "fantasypros": round(fantasypros_err, 2), "fantasypros_abs": abs(round(fantasypros_err, 2)), "yahoo_proj": yahoo_proj, "espn_proj": espn_proj, "fantasypros_proj": fantasypros_proj, "espn_proj_next": espn_proj_next, "yahoo_proj_next": yahoo_proj_next, "fantasypros_proj_next": fantasypros_proj_next})
		#print("{}:{}\t{} {}\t{} {}".format(player,actual,yahoo_proj,round(yahoo_err, 2),espn_proj,round(espn_err, 2)))

	graphs = []
	# Graph: Player x % ERR
	graph = {"title": "Most Accurate Projections ["+pos+"] (sorted by Yahoo accuracy)", "actual": [], "espn": [], "yahoo": [], "fantasypros": [], "espn_proj": [], "yahoo_proj": [], "fantasypros_proj": [], "yahoo_proj_next": [], "espn_proj_next": [], "fantasypros_proj_next": [], "text": [], "espn_avg_err": 0, "yahoo_avg_err": 0, "fantasypros_avg_err": 0, "yahoo_over": 0, "espn_over": 0, "fantasypros_over": 0, "div": "plot_div"}
	error_sorted = sorted(proj_error, key=operator.itemgetter("yahoo_abs"))
	espn_error_sorted = sorted(proj_error, key=operator.itemgetter("espn_abs"))
	fantasypros_error_sorted = sorted(proj_error, key=operator.itemgetter("fantasypros_abs"))

	espn_sorted_str = ""
	yahoo_sorted_str = ""
	fantasypros_sorted_str = ""
	s = []
	for player in error_sorted:
		if player["position"] == pos:
			spl = ' '.join(player["text"].split(" ")[1:])
			s.append(spl.title())

	yahoo_sorted_str = ', '.join(s[:15])
	s = []
	for player in espn_error_sorted:
		if player["position"] == pos:
			spl = ' '.join(player["text"].split(" ")[1:])
			s.append(spl.title())

	espn_sorted_str = ', '.join(s[:15])
	s = []
	for player in fantasypros_error_sorted:
		if player["position"] == pos:
			spl = ' '.join(player["text"].split(" ")[1:])
			s.append(spl.title())

	fantasypros_sorted_str = ', '.join(s[:15])

	espn_over = 0
	yahoo_over = 0
	fantasypros_over = 0
	espn_avg_err = 0
	yahoo_avg_err = 0
	fantasypros_avg_err = 0
	i = 0
	
	total_espn_proj = 0
	total_yahoo_proj = 0
	total_fantasypros_proj = 0
	for player in error_sorted:
		#if player["position"] == "TE":
		min_num = 0
		max_num = 100
		#if (player["espn_proj"] >= min_num and player["espn_proj"] <= max_num) or (player["yahoo_proj"] >= min_num and player["yahoo_proj"] <= max_num):
		if pos == "ALL" or player["position"] == pos:

			for key in ["text", "actual", "espn", "yahoo", "fantasypros", "espn_proj", "yahoo_proj", "fantasypros_proj", "espn_proj_next", "yahoo_proj_next", "fantasypros_proj_next"]:
				if key == "text":
					graph[key].append(player[key])
				else:
					graph[key].append(str(player[key]))
			espn_avg_err += abs(player["espn"])
			yahoo_avg_err += abs(player["yahoo"])
			fantasypros_avg_err += abs(player["fantasypros"])

			total_yahoo_proj += player["yahoo_proj"]
			total_espn_proj += player["espn_proj"]
			total_fantasypros_proj += player["fantasypros_proj"]
			if player["yahoo"] > 0:
				yahoo_over += 1
			if player["espn"] > 0:
				espn_over += 1
			if player["fantasypros"] > 0:
				fantasypros_over += 1

	total_players = len(graph["text"])
	comma = ","
	espn_avg_err /= total_players
	yahoo_avg_err /= total_players
	fantasypros_avg_err /= total_players
	espn_under = total_players - espn_over
	yahoo_under = total_players - yahoo_over
	fantasypros_under = total_players - fantasypros_over

	for key in ["text", "actual", "espn", "yahoo", "fantasypros", "espn_proj", "yahoo_proj", "fantasypros_proj", "espn_proj_next", "yahoo_proj_next", "fantasypros_proj_next"]:
		graph[key] = comma.join(graph[key])
	graphs.append(graph)

	if pos == "ALL":
		print("TOTAL ({} players)\n".format(total_players))
		if espn_avg_err < yahoo_avg_err and espn_avg_err < fantasypros_avg_err:
			print("- **ESPN: (1 - {}% Error) = {}% Accuracy**".format(round(espn_avg_err, 2), 100 - round(espn_avg_err, 2)))
		else:
			print("- ESPN: (1 - {}% Error) = {}% Accuracy".format(round(espn_avg_err, 2), 100 - round(espn_avg_err, 2)))

		if yahoo_avg_err < espn_avg_err and yahoo_avg_err < fantasypros_avg_err:
			print("- **Yahoo: (1 - {}% Error) = {}% Accuracy**".format(round(yahoo_avg_err, 2), 100 - round(yahoo_avg_err, 2)))
		else:
			print("- Yahoo: (1 - {}% Error) = {}% Accuracy".format(round(yahoo_avg_err, 2), 100 - round(yahoo_avg_err, 2)))

		if fantasypros_avg_err < espn_avg_err and fantasypros_avg_err < yahoo_avg_err:
			print("- **FantasyPros: (1 - {}% Error) = {}% Accuracy**".format(round(fantasypros_avg_err, 2), 100 - round(fantasypros_avg_err, 2)))
		else:
			print("- FantasyPros: (1 - {}% Error) = {}% Accuracy".format(round(fantasypros_avg_err, 2), 100 - round(fantasypros_avg_err, 2)))

		print("- Total ESPN Projected: {}".format(total_espn_proj))
		print("- Total Yahoo Projected: {}".format(total_yahoo_proj))
		print("- Total FantasyPros Projected: {}".format(total_fantasypros_proj))
	else:
		print("[{} ({} players)](imgur)\n".format(pos, total_players))
		if espn_avg_err < yahoo_avg_err and espn_avg_err < fantasypros_avg_err:
			print("- **ESPN: {}% Accuracy**".format(100 - round(espn_avg_err, 2)))
		else:
			print("- ESPN: {}% Accuracy".format(100 - round(espn_avg_err, 2)))
		print("> {}\n".format(espn_sorted_str))

		if yahoo_avg_err < espn_avg_err and yahoo_avg_err < fantasypros_avg_err:
			print("- **Yahoo: {}% Accuracy**".format(100 - round(yahoo_avg_err, 2)))
		else:
			print("- Yahoo: {}% Accuracy".format(100 - round(yahoo_avg_err, 2)))
		print("> {}\n".format(yahoo_sorted_str))

		if fantasypros_avg_err < espn_avg_err and fantasypros_avg_err < yahoo_avg_err:
			print("- **FantasyPros: {}% Accuracy**".format(100 - round(fantasypros_avg_err, 2)))
		else:
			print("- FantasyPros: {}% Accuracy".format(100 - round(fantasypros_avg_err, 2)))
		print("> {}\n".format(fantasypros_sorted_str))
	"""
	graph = {"name": "Percent Error Vs. Projected (Yahoo)", "x": [], "y": [], "y_arr_plus": [], "y_arr_minus": []}
	for error in proj_error:
		graph["x"].append(str(error["yahoo_proj"]))
		graph["y"].append(str(error["actual"]))

		if error["yahoo"] > 0:
			graph["y_arr_plus"].append(str(error["yahoo"]))
			graph["y_arr_minus"].append("0")
		elif error["yahoo"] < 0:
			graph["y_arr_plus"].append("0")
			graph["y_arr_minus"].append(str(error["yahoo"]))
	comma = ","
	graph["x"] = comma.join(graph["x"])
	graph["y"] = comma.join(graph["y"])
	graph["y_arr_plus"] = comma.join(graph["y_arr_plus"])
	graph["y_arr_minus"] = comma.join(graph["y_arr_minus"])
	graphs.append(graph)

	with open("static/graphs/projected_vs_error_yahoo.csv", "w") as fh:
		for error in proj_error:
			fh.write("{},{}".format(error["yahoo_proj"],error["yahoo"]))

	with open("static/graphs/projected_vs_error_espn.csv", "w") as fh:
		for error in proj_error:
			fh.write("{},{}".format(error["yahoo_proj"],error["yahoo"]))
	"""

	# Graph: Projected x Actual
	return render_template("graphs.html", graphs=graphs, espn_over_under="{}/{}".format(espn_over,espn_under), yahoo_over_under="{}/{}".format(yahoo_over,yahoo_under), fantasypros_over_under="{}/{}".format(fantasypros_over,fantasypros_under), espn_average_error="{}%".format(round(espn_avg_err, 2)), yahoo_average_error="{}%".format(round(yahoo_avg_err, 2)), fantasypros_average_error="{}%".format(round(fantasypros_avg_err, 2)))


