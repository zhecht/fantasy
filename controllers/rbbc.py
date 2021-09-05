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
    return render_template("rbbc.html", curr_week=curr_week)
