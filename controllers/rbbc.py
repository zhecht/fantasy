#from selenium import webdriver
from flask import *
from subprocess import call
from bs4 import BeautifulSoup as BS
from sys import platform
from datetime import datetime

import json
import math
import operator
import os
import subprocess
import re

from controllers.functions import *
import controllers.redzone

rbbc_print = Blueprint('rbbc', __name__, template_folder='views')

prefix = ""
if os.path.exists("/home/zhecht/fantasy"):
    # if on linux aka prod
    prefix = "/home/zhecht/fantasy/"

@rbbc_print.route("/getRBBC")
def getRBBC():
    rbbcResult = []
    snap_trends = controllers.redzone.get_redzone_trends(RBBC_TEAMS, curr_week, "RB")
    for team in RBBC_TEAMS:
        team_display = TEAM_TRANS[team] if team in TEAM_TRANS else team
        playerList = []
        players = snap_trends[team].keys()
        for player in players:
            playerData = snap_trends[team][player]
            rbbcResult.append({
                "player": player.title(),
                "team": team_display.upper(),
                "avgSnapPer": playerData["avg_snaps"],
                "looksPerGame": playerData["looks_per_game"],
                "looksPerGameTrend": playerData["looks_per_game_trend"],
                "looksSharePer": playerData["looks_share"],
                "looksShareTrend": playerData["looks_share_trend"],
                "targetsPerGame": playerData["targets_per_game"],
                "targetsPerGameTrend": playerData["targets_per_game_trend"],
                "targetShare": playerData["target_share"],
                "targetShareTrend": playerData["target_share_trend"],
            })
    return jsonify(rbbcResult)

@rbbc_print.route('/rbbc')
def rbbc_route():
    snap_trends = controllers.redzone.get_redzone_trends(RBBC_TEAMS, curr_week, "RB", is_ui=True)

    table = f"<table id='rbbc_table'>"
    table += f"<thead><tr><th colspan='7'>Running Back Breakdowns</th></tr><tr>"
    for header in ["Player", "Team", "Avg Snap %", "RZ Looks Per Game", "RZ Looks Share", "Targets Per Game", "RB TGT Share"]:
        table += f"<th>{header}</th>"
    table += "</tr></thead><tbody>"
    for team in RBBC_TEAMS:
        team_display = TEAM_TRANS[team] if team in TEAM_TRANS else team
        extra = ""
        players_ordered = []
        players = snap_trends[team].keys()
        for player in players:
            players_ordered.append({"player": player, "avg_snaps": snap_trends[team][player]["avg_snaps"]})
        for player in sorted(players_ordered, key=operator.itemgetter("avg_snaps"), reverse=True):
            player = player["player"]
            if snap_trends[team][player]["snaps"] == 0:
                if snap_trends[team][player]["looks_per_game"] == 0 and snap_trends[team][player]["targets_per_game"] == 0:
                    continue
                extra += f"<tr><td class='{team}'>{player.title()}</td><td class='{team}'>{team_display.upper()}</td><td>{snap_trends[team][player]['avg_snaps']}% (DNP)</td><td>{snap_trends[team][player]['looks_per_game']}</td><td>{snap_trends[team][player]['looks_share']}%</td><td>{snap_trends[team][player]['targets_per_game']}</td><td>{snap_trends[team][player]['target_share']}%</td></tr>"
            else:
                if snap_trends[team][player]["total_looks"] == 0 and snap_trends[team][player]["total_targets"] == 0:
                    pass
                    #continue
                table += f"<tr><td class='{team}'>{player.title()}</td><td class='{team}'>{team_display.upper()}</td><td>{snap_trends[team][player]['avg_snaps']}% ({snap_trends[team][player]['snaps_per_game_trend']}%)</td><td>{snap_trends[team][player]['looks_per_game']} ({snap_trends[team][player]['looks_per_game_trend']})</td><td>{snap_trends[team][player]['looks_share']}% ({snap_trends[team][player]['looks_share_trend']})</td><td>{snap_trends[team][player]['targets_per_game']} ({snap_trends[team][player]['targets_per_game_trend']})</td><td>{snap_trends[team][player]['target_share']}% ({snap_trends[team][player]['target_share_trend']})</td></tr>"
        # print DNP on bottotm
        table += extra
    table += "</tbody></table>"
    return render_template("rbbc.html", table=table, curr_week=curr_week)
