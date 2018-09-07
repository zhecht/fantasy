from flask import *


from lxml import etree
#from sql_helper import *
import controllers.constants
import operator

try:
	import controllers.constants as constants
	import controllers.read_rosters as read_rosters
	import controllers.helper as helper
	import controllers.news as news
	import controllers.stats as stats
	import controllers.espn_stats as espn_stats
	from controllers.oauth import *
except:
	import constants
	import read_rosters
	import helper
	import news
	import stats
	import espn_stats
	from oauth import *

team = Blueprint('team', __name__, template_folder='views')

teams_not_played = ["NYJ", "DET", "LAR", "OAK"]

@team.route('/team/<teamnum>')
def team_route(teamnum):
	oauth = MyOAuth()
	teamnum = int(teamnum)
	curr_week = 1

	if request.args.get("week"):
		curr_week = int(request.args.get("week"))

	players_on_FA = read_rosters.read_FA()
	if teamnum == 0:
		players_on_teams = players_on_FA
	else:
		players_on_teams, name_translations = read_rosters.read_rosters()
		players_on_teams_sorted = sorted(players_on_teams.items(), key=lambda x: x[1]["fantasy_position"])

	all_teams = read_rosters.read_standings()
	if teamnum == 0:
		teamname = "FA"
	else:
		teamname = all_teams[teamnum-1]['name']

	#player_news = news.read_news(players_on_teams, players_on_FA, all_teams)
	espn_proj_json = espn_stats.read_espn_stats(curr_week, curr_week + 1)
	yahoo_proj_json = stats.read_yahoo_stats(curr_week, curr_week + 1)
	actual_json = stats.read_actual_stats(curr_week, curr_week + 1)
	snap_counts = helper.getSnapCounts(curr_week + 1)
	all_players = []

	for player in players_on_teams:
		if players_on_teams[player]["team_id"] != teamnum or players_on_teams[player]["position"] == "K" or players_on_teams[player]["position"] == "DEF" or players_on_teams[player]["nfl_team"] in teams_not_played:
			continue
		try:
			espn_proj = espn_proj_json[player]
			yahoo_proj = yahoo_proj_json[player]
			actual = actual_json[player]
		except:
			continue

		yahoo_accuracy, espn_accuracy, total_over, total_under, fppg = helper.getAccuracy(curr_week, yahoo_proj, espn_proj, actual)
		comma = ","
		weekly_act = actual
		weekly_proj = yahoo_proj
		weekly_proj_espn = espn_proj

		last_week_snaps = snap_counts[player]["last_week"]
		trend_str = str(snap_counts[player]["trend"])
		trend_class = "neutral"
		trend = snap_counts[player]["trend"]

		if trend < 0:
			trend_class = "negative"
		elif trend > 0:
			trend_class = "positive"
			trend_str = "+"+trend_str

		"""
		accuracy,espn_accuracy,total_over,total_under,fppg,weekly_proj,weekly_act = getAccuracy(pid, curr_week)
		weekly_proj_espn = getWeeklyESPN(pid, curr_week)
		snap_counts, last_week_snaps, trend = getSnapCounts(pid, curr_week)
		trend_class = "neutral"
		trend_str = str(trend)
		if trend < 0:
			trend_class = "negative"
		elif trend > 0:
			trend_class = "positive"
			trend_str = "+"+trend_str

		if both_proj == None:
			proj = 0
			espn_proj = 0
		else:
			proj = both_proj[0][0]
			espn_proj = both_proj[0][1]
		"""
		#all_players.append({"id": players_on_teams[player]["pid"], "full": player, "pos": players_on_teams[player]["position"], "yahoo_proj": yahoo_proj, "espn_proj": espn_proj, "yahoo_acc": yahoo_accuracy, "espn_acc": espn_accuracy, "proj_under": total_under, "proj_over": total_over, "fppg": fppg, "weekly_proj": weekly_proj, "weekly_act": weekly_act, "weekly_proj_espn": weekly_proj_espn, "snap_counts": snap_counts[player]["counts"], "last_week_snaps": last_week_snaps, "snap_trend": trend_str, "snap_trend_class": trend_class, "news": player_news[player]})
		all_players.append({"id": players_on_teams[player]["pid"], "full": player, "pos": players_on_teams[player]["position"], "yahoo_proj": yahoo_proj, "espn_proj": espn_proj, "yahoo_acc": yahoo_accuracy, "espn_acc": espn_accuracy, "proj_under": total_under, "proj_over": total_over, "fppg": fppg, "weekly_proj": weekly_proj, "weekly_act": weekly_act, "weekly_proj_espn": weekly_proj_espn, "snap_counts": snap_counts[player]["counts"], "last_week_snaps": last_week_snaps, "snap_trend": trend_str, "snap_trend_class": trend_class, "news": []})

	
	return render_template("main.html", players=all_players, teams=all_teams, teamname=teamname, curr_team=teamnum)

