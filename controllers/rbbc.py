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

import controllers.redzone

rbbc_print = Blueprint('rbbc', __name__, template_folder='views')

prefix = ""
if os.path.exists("/home/zhecht/fantasy"):
    # if on linux aka prod
    prefix = "/home/zhecht/fantasy/"

curr_week = 15

@rbbc_print.route('/rbbc')
def rbbc_route():
    team_trans = {"rav": "bal", "htx": "hou", "oti": "ten", "sdg": "lac", "ram": "lar", "clt": "ind", "crd": "ari", "gnb": "gb", "kan": "kc", "nwe": "ne", "rai": "lv", "sfo": "sf", "tam": "tb", "nor": "no"}
    afc_teams = ['rav', 'buf', 'cin', 'cle', 'den', 'htx', 'clt', 'jax', 'kan', 'sdg', 'rai', 'mia', 'nwe', 'nyj', 'pit', 'ten']
    nfc_teams = ['crd', 'atl', 'car', 'chi', 'dal', 'det', 'gnb', 'ram', 'min', 'nor', 'nyg', 'phi', 'sea', 'sfo', 'tam', 'was']
    rbbc_teams = ['crd', 'atl', 'rav', 'buf', 'car', 'chi', 'cin', 'cle', 'dal', 'den', 'det', 'gnb', 'htx', 'clt', 'jax', 'kan', 'sdg', 'ram', 'rai', 'mia', 'min', 'nor', 'nwe', 'nyg', 'nyj', 'phi', 'pit', 'sea', 'sfo', 'tam', 'oti', 'was']
    snap_trends = controllers.redzone.get_redzone_trends(rbbc_teams, curr_week, "RB", is_ui=True)
    table = ""

    #table += "<div id='team_click_div'><a class='team_click' href='#'>All</a>"
    #for team in rbbc_teams:
    #    team_display = team_trans[team] if team in team_trans else team
    #    table += f"<a class='team_click' href='#'>{team_display}</a>"
    #table += "</div>"
    for team in rbbc_teams:
        team_display = team_trans[team] if team in team_trans else team
        table += f"<table id='{team}_table'>"
        table += f"<thead><tr><th class='{team}' colspan='6'>{team_display.upper()}</th></tr><tr>"
        for header in ["Player", "Avg Snap %", "RZ Looks Per Game", "RZ Looks Share", "Targets Per Game", "RB TGT Share"]:
            table += f"<th class='{team}'>{header}</th>"
        table += "</tr></thead><tbody>"
        extra = ""
        players_ordered = []
        players = snap_trends[team].keys()
        for player in players:
            players_ordered.append({"player": player, "avg_snaps": snap_trends[team][player]["avg_snaps"]})
        for player in sorted(players_ordered, key=operator.itemgetter("avg_snaps"), reverse=True):
            player = player["player"]
            if "jackson" in player:
                print(player)
            if snap_trends[team][player]["snaps"] == 0:
                if snap_trends[team][player]["looks_per_game"] == 0 and snap_trends[team][player]["targets_per_game"] == 0:
                    continue
                extra += f"<tr><td class='{team}'>{player.title()}</td><td class='{team}'>{snap_trends[team][player]['avg_snaps']}% (DNP)</td><td class='{team}'>{snap_trends[team][player]['looks_per_game']}</td><td class='{team}'>{snap_trends[team][player]['looks_share']}%</td><td class='{team}'>{snap_trends[team][player]['targets_per_game']}</td><td class='{team}'>{snap_trends[team][player]['target_share']}%</td></tr>"
            else:
                if snap_trends[team][player]["total_looks"] == 0 and snap_trends[team][player]["total_targets"] == 0:
                    pass
                    #continue
                table += f"<tr><td class='{team}'>{player.title()}</td><td class='{team}'>{snap_trends[team][player]['avg_snaps']}% ({snap_trends[team][player]['snaps_per_game_trend']}%)</td><td class='{team}'>{snap_trends[team][player]['looks_per_game']} ({snap_trends[team][player]['looks_per_game_trend']})</td><td class='{team}'>{snap_trends[team][player]['looks_share']}% ({snap_trends[team][player]['looks_share_trend']})</td><td class='{team}'>{snap_trends[team][player]['targets_per_game']} ({snap_trends[team][player]['targets_per_game_trend']})</td><td class='{team}'>{snap_trends[team][player]['target_share']}% ({snap_trends[team][player]['target_share_trend']})</td></tr>"
        # print DNP on bottotm
        table += extra
        table += "</tbody></table>"
        # ranks
    return render_template("rbbc.html", table=table, curr_week=curr_week)
