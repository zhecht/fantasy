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

from controllers.redzone import *

rbbc_print = Blueprint('rbbc', __name__, template_folder='views')

prefix = ""
if os.path.exists("/home/zhecht/fantasy"):
    # if on linux aka prod
    prefix = "/home/zhecht/fantasy/"

curr_week = 4

@rbbc_print.route('/rbbc')
def rbbc_route():
    team_trans = {"rav": "bal", "htx": "hou", "oti": "ten", "sdg": "lac", "ram": "lar", "clt": "ind", "crd": "ari", "gnb": "gb", "kan": "kc", "nwe": "ne", "rai": "lv", "sfo": "sf", "tam": "tb", "nor": "no"}
    rbbc_teams = ['crd', 'atl', 'rav', 'buf', 'car', 'chi', 'cin', 'cle', 'dal', 'den', 'det', 'gnb', 'htx', 'clt', 'jax', 'kan', 'sdg', 'ram', 'rai', 'mia', 'min', 'nor', 'nwe', 'nyg', 'nyj', 'phi', 'pit', 'sea', 'sfo', 'tam', 'oti', 'was']
    snap_trends = get_redzone_trends(rbbc_teams, curr_week, "RB")
    table = ""
    for team in rbbc_teams:
        team_display = team_trans[team] if team in team_trans else team
        table += f"<table id='{team}_table'>"
        table += f"<thead><tr><th colspan='6'>{team_display.upper()}</th></tr><tr>"
        for header in ["Player", "Snap%", "RZ Looks", "RZ Looks Share", "TGTS", "RB TGT Share"]:
            table += f"<th>{header}</th>"
        table += "</tr></thead><tbody>"
        extra = ""
        for player in snap_trends[team]:
            if snap_trends[team][player]["snaps"] == 0:
                if snap_trends[team][player]["total_looks"] == 0 :
                    continue
                extra += "<tr><td>{}</td><td>DNP</td><td>{}</td><td>{}%</td><td>{}</td><td>{}%</td></tr>".format(
                    player,
                    snap_trends[team][player]["total_looks"],
                    snap_trends[team][player]["looks_share"],
                    snap_trends[team][player]["total_targets"],
                    snap_trends[team][player]["target_share"]
                )
            else:
                if snap_trends[team][player]["total_looks"] == 0 and snap_trends[team][player]["total_targets"] == 0:
                    pass
                    #continue
                table += "<tr><td>{}</td><td>{}% ({})</td><td>{} ({})</td><td>{}% ({})</td><td>{} ({})</td><td>{}% ({})</td></tr>".format(
                    player,
                    snap_trends[team][player]["snaps"], snap_trends[team][player]["snaps_trend"],
                    snap_trends[team][player]["total_looks"], snap_trends[team][player]["looks_trend"],
                    snap_trends[team][player]["looks_share"], snap_trends[team][player]["looks_share_trend"],
                    snap_trends[team][player]["total_targets"], snap_trends[team][player]["target_trend"],
                    snap_trends[team][player]["target_share"], snap_trends[team][player]["target_share_trend"]
                )
        # print DNP on bottotm
        table += extra
        table += "</tbody></table>"
        # ranks
    return render_template("rbbc.html", table=table)
