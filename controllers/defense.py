#from selenium import webdriver
from flask import *
from subprocess import call
from bs4 import BeautifulSoup as BS
from sys import platform
from base64 import b64encode
from datetime import datetime

#from selenium.webdriver.firefox.options import Options

import json
import math
import operator
import os
import subprocess
import re

try:
    import controllers.profootballreference as profootballreference
except:
    import profootballreference

try:
    import urllib2 as urllib
except:
    import urllib.request as urllib

defense_print = Blueprint('defense', __name__, template_folder='views')

prefix = ""
if platform != "darwin":
    # if on linux aka prod
    prefix = "/home/zhecht/fantasy/"

# goes from green -> yellow -> orange -> red

team_trans = {"rav": "bal", "htx": "hou", "oti": "ten", "sdg": "lac", "ram": "lar", "rai": "oak", "clt": "ind", "crd": "ari"}

def merge_two_dicts(x, y):
    z = x.copy()
    z.update(y)
    return z

RANKS_COLORS = []

def get_closest_rgb(rgbs, idx):
    #return ""
    idx = int(idx)
    if str(idx) in rgbs:
        return rgbs[str(idx)]
    for close_idx in range(3):
        if str(idx - close_idx) in rgbs:
            return rgbs[str(idx - close_idx)]
        elif str(idx + close_idx) in rgbs:
            return rgbs[str(idx + close_idx)]
    return ""

# split all the colors up based on total. E.g. total=32 for all teams. Split @ every 100 / 32
def get_ranks_colors(total):
    rgbs = {}
    with open("{}static/rgbs.json".format(prefix)) as fh:
        rgbs = json.loads(fh.read())
    step = math.floor(100 / total)
    start = 100
    while start > 0:
        color = get_closest_rgb(rgbs, start)
        #print(color)
        RANKS_COLORS.append(color)
        start -= step
    return

def get_suffix(num):
    if num >= 11 and num <= 13:
        return "th"
    elif num % 10 == 1:
        return "st"
    elif num % 10 == 2:
        return "nd"
    elif num % 10 == 3:
        return "rd"
    return "th"

def get_ranks_style(rank, extra=None):
    if extra:
        return "style='background-color: rgb({});{}'".format(RANKS_COLORS[rank - 1], extra)
    return "style='background-color: rgb({});'".format(RANKS_COLORS[rank - 1])

def get_ranks_html(settings, curr_week = 11):
    ranks, defense_tot = profootballreference.get_ranks(curr_week, settings)
    get_ranks_colors(32)

    scoring = settings["ppr"]
    defense_ranks = {}
    html = "<table id='ppg_by_pos'>"
    html += "<tr><th colspan='12'>Points Allowed Per Game Per Position ({} PPR)</th></tr>".format(scoring)
    html += "<tr><th class='QB_td'>Team</th><th class='QB_td'>QB</th><th class='RB_td'>Team</th><th class='RB_td'>RB</th><th class='WR_td'>Team</th><th class='WR_td'>WR</th><th class='TE_td'>Team</th><th class='TE_td'>TE</th><th class='K_td'>Team</th><th class='K_td'>K</th><th class='DEF_td'>Team</th><th class='DEF_td'>DEF</th></tr>"
    # sorted by pos
    for idx in range(32):
        html += "<tr>"
        style = get_ranks_style(idx + 1)
        for pos in ["QB", "RB", "WR", "TE", "K", "DEF"]:
            sorted_ranks = sorted(defense_tot, key=operator.itemgetter("{}_ppg".format(pos)), reverse=True)

            arr = sorted_ranks[idx]
            display_team = arr["team"]
            if display_team in team_trans:
                display_team = team_trans[display_team]

            if display_team not in defense_ranks:
                defense_ranks[display_team] = {}
            if pos not in defense_ranks[display_team]:
                defense_ranks[display_team][pos] = 0
                defense_ranks[display_team]["{}_rank".format(pos)] = 0
            defense_ranks[display_team][pos] = arr["{}_ppg".format(pos)]
            defense_ranks[display_team]["{}_rank".format(pos)] = idx + 1

            html += "<td class='clickable {}_td'>{}</td><td id='{}_{}' class='clickable {}_td' {}>{}</td>".format(pos, display_team.upper(), display_team, pos, pos, style, arr["{}_ppg".format(pos)])
        html += "</tr>"
    html += "</table>"
    
    sorted_teams = sorted(defense_ranks.keys())
    html += "<table id='ppg_by_team'>"
    html += "<tr><th colspan='8'>Points Allowed Per Game ({} PPR)</th></tr>".format(scoring)
    html += "<tr><th>Team</th><th class='QB_td'>QB</th><th class='RB_td'>RB</th><th class='WR_td'>WR</th><th class='TE_td'>TE</th><th class='K_td'>K</th><th class='DEF_td'>DEF</th><th> Opp</th></tr>".format(curr_week)
    for team in sorted_teams:
        opp_team = profootballreference.get_opponents(team)[curr_week]
        html += "<tr><td>{}</td>".format(team.upper())
        for pos in ["QB", "RB", "WR", "TE", "K", "DEF"]:
            r = defense_ranks[team]["{}_rank".format(pos)]
            style = get_ranks_style(r, extra="position:relative;z-index:-1;")
            span = "<span style='position:absolute;bottom:0;right:5px;font-size:10px;'>{}{}</span>".format(r, get_suffix(r))
            html += "<td class='clickable {}_td' id='{}_{}' {}>{}{}</td>".format(pos, team, pos, style, defense_ranks[team][pos], span)
        opp_team = team_trans[opp_team] if opp_team in team_trans else opp_team
        html += "<td>{}</td></tr>".format(opp_team.upper())
    html += "</table>"
    return html, sorted_teams

def get_color_html():
    html = "<table><tr>"
    for idx, rgb in enumerate(RANKS_COLORS):
        color = RANKS_COLORS[idx]
        html += "<th style='color: rgb({});'>{}</th>".format(color, idx + 1)
    html += "</tr></table>"

    html = "<table><tr>"
    for idx, rgb in enumerate(RANKS_COLORS):
        style = get_ranks_style(idx + 1)
        html += "<th {}></th>".format(style)
    html += "</tr></table>"
    return html

# get html for each clickable overview
def get_html(team_arg, pos, opp):
    def_txt = "OFF" if pos == "DEF" else "DEF"
    html = "<table class='click_tables' id='{}_{}_table'>".format(team_arg, pos)
    mobile_html = "<table class='click_tables' id='{}_{}_mobile_table'>".format(team_arg, pos)

    if pos == "DEF":
        html += "<tr><th colspan='2' style='position:relative;'><span class='close_table'>X</span>DEF Vs. {} {}</th></tr>".format(team_arg.upper(), def_txt)
        mobile_html += "<tr><th style='position:relative;'><span class='close_table'>X</span>DEF Vs. {} {}</th></tr>".format(team_arg.upper(), def_txt)
    else:
        html += "<tr><th colspan='2' style='position:relative;'><span class='close_table'>X</span>{} {} Vs. {}</th></tr>".format(team_arg.upper(), def_txt, pos)
        mobile_html += "<tr><th style='position:relative;'><span class='close_table'>X</span>{} {} Vs. {}</th></tr>".format(team_arg.upper(), def_txt, pos)

    for idx, arr in enumerate(opp):
        players_html = "<table class='players_table'>"
        players_mobile_html = "<table class='players_table'>"
        team = ""
        total = 0
        sched = profootballreference.get_opponents(arr["team"])
        for player_idx, p in enumerate(arr["players"]):
            m = re.match(r"wk(\d+) (.*): (.*) pts \((.*)\)", p)
            wk = int(m.group(1)) + 1
            team = m.group(2)
            name_pts = m.group(3)
            stats = m.group(4)
            pts = round(float(name_pts.split(" ")[-1]), 2)
            total += pts
            name = ' '.join(name_pts.split(" ")[:-1])
            player_id = "{}_vs_{}_{}_{}".format(team_arg, team, pos, player_idx)
            if team in team_trans:
                team = team_trans[team]
            if pos == "DEF":
                players_html += "<tr><td style='width: 90px;padding-left:10px;'>{} pts</td><td>{}</td></tr>".format(pts, stats)
                players_mobile_html += "<tr><td style='width: 90px;padding-left:10px;'>{} pts</td><td><a class='mobile_show_stats' href='#' id='{}'>Show</a></td></tr><tr><td colspan='3' style='display: none;text-align: center;' id='{}_stats'>[ {} ]</td></tr>".format(pts, player_id, player_id, stats)
            else:
                players_html += "<tr><td style='width: 90px;padding-left:10px;'>{} pts</td><td style='width: 175px;'>{}</td><td>{}</td></tr>".format(pts, name.title(), stats)
                players_mobile_html += "<tr><td style='width: 90px;padding-left:10px;'>{} pts</td><td style='width: 175px;'>{}</td><td><a class='mobile_show_stats' href='#' id='{}'>Show</a></td></tr><tr><td colspan='3' style='display: none;text-align: center;' id='{}_stats'>[ {} ]</td></tr>".format(pts, name.title(), player_id, player_id, stats)

        players_html += "</table>"
        players_mobile_html += "</table>"
        tot = ""
        mobile_tot = ""
        if pos not in ["QB", "DEF"]:
            tot = "<br>{} pts".format(round(total, 2))
            mobile_tot = "{} pts".format(round(total, 2))
        
        if arr["players"] == "":
            if sched[idx] == "BYE":
                html += "<tr><td style='width:100px;'>wk{} BYE</td><td></td></tr>".format(idx + 1)
                mobile_html += "<tr><td style='width:100px;'>wk{} BYE</td></tr>".format(idx + 1)
            else:
                html += "<tr><td style='width:100px;'>wk{} {}</td><td>-</td></tr>".format(idx + 1, arr["opp_team"].upper())
                mobile_html += "<tr><td style='width:100px;'>wk{} {}</td></tr><tr><td>-</td></tr>".format(idx + 1, arr["opp_team"].upper())
        else:
            html += "<tr><td style='width:100px;'>wk{} {}{}</td><td>{}</td></tr>".format(wk, team.upper(), tot, players_html)
            mobile_html += "<tr><td style='width: 100%;'>wk{} {}: {}</td></tr><tr><td>{}</td></tr>".format(wk, team.upper(), mobile_tot, players_mobile_html)
    mobile_html += "</table>"
    html += "</table>"
    return html+mobile_html

def get_team_html(teams, settings):
    curr_week = 11
    ranks = profootballreference.get_ranks(curr_week, settings)

    html = ""
    for team in teams:
        for pos in ["QB", "RB", "WR", "TE", "K", "DEF"]:
            opp, tot = profootballreference.position_vs_opponent_stats(team, pos, ranks, settings)
            html += get_html(team, pos, opp[:curr_week])
    return html

def get_scoring_data(which):
    data = []
    if which == "offense":
        data = [
            {"key": "pass_yds", "type": "select", "options": [1, 10, 25, 50, 100], "default": 25},
            {"key": "rush_yds", "type": "select", "options": [1,5,10,15,20,25], "default": 10},
            {"key": "rec_yds", "type": "select", "options": [1,5,10,15,20,25], "default": 10},
            {"key": "pass_int", "type": "button", "options": [0,-1,-2], "default": -2},
            {"key": "fumbles_lost", "type": "button", "options": [0,-1,-2], "default": -2},
            {"key": "pass_tds", "type": "button", "options": [4,6], "default": 4},
            {"key": "rush_tds", "type": "button", "options": [4,6], "default": 6},
            {"key": "rec_tds", "type": "button", "options": [4,6], "default": 6},
        ]
    elif which == "kicking":
        data = [
            {"key": "xpm", "type": "select", "options": [0,1], "default": 1},
            {"key": "field_goal_0-19", "type": "select", "options": [3,4,5], "default": 3},
            {"key": "field_goal_20-29", "type": "select", "options": [3,4,5], "default": 3},
            {"key": "field_goal_30-39", "type": "select", "options": [3,4,5], "default": 3},
            {"key": "field_goal_40-49", "type": "select", "options": [3,4,5], "default": 4},
            {"key": "field_goal_50+", "type": "select", "options": [3,4,5], "default": 5},
        ]
    elif which == "defense":
        data = [
            {"key": "sack", "type": "button", "options": [0,1], "default": 1},
            {"key": "interception", "type": "button", "options": [0,1,2], "default": 2},
            {"key": "fumble_recovery", "type": "button", "options": [0,1,2], "default": 2},
            {"key": "safety", "type": "button", "options": [0,1,2], "default": 2},
            {"key": "touchdown", "type": "button", "options": [0,4,6], "default": 6},
            {"key": "0_points_allowed", "type": "select", "options": [0,1,2,3,4,5,6,7,8,9,10,15], "default": 10},
            {"key": "1-6_points_allowed", "type": "select", "options": [0,1,2,3,4,5,6,7], "default": 7},
            {"key": "7-13_points_allowed", "type": "select", "options": [0,1,2,3,4,5], "default": 4},
            {"key": "14-20_points_allowed", "type": "select", "options": [0,1,2,3,4,5], "default": 1},
            {"key": "21-27_points_allowed", "type": "select", "options": [-2,-1,0,1,2,3,4,5], "default": 0},
            {"key": "28-34_points_allowed", "type": "select", "options": [-2,-1,0,1,2,3,4,5], "default": -1},
            {"key": "35+_points_allowed", "type": "select", "options": [-6,-5,-4,-3,-2,-1,0,1], "default": -4},
        ]
    return data

def default_settings():
    settings = {"ppr": 0.5}
    for which in ["offense", "kicking", "defense"]:
        get_scoring(which, settings)
    return settings

def init_settings(filename):
    if filename == "default":
        return default_settings()
    filename = filename[:-5] # cut off .html
    settings_arr = filename.split("_")[2:]
    settings = {"ppr": float(settings_arr[0])}
    curr_idx = 1
    for which in ["offense", "kicking", "defense"]:
        data = get_scoring_data(which)
        for arr in data:
            settings[arr["key"]] = int(settings_arr[curr_idx])
            curr_idx += 1
    return settings

def get_settings_filename(settings):
    # {'pass_yds': 25, .... }
    filename = "click_html_{}".format(settings["ppr"])
    curr_idx = 1
    for which in ["offense", "kicking", "defense"]:
        data = get_scoring_data(which)
        for arr in data:
            filename += "_{}".format(settings[arr["key"]])

    #for key in settings:
    #    filename += "_{}".format(settings[key])
    return "{}.html".format(filename)

def read_scoring_settings():
    with open("{}static/scoring_settings.json".format(prefix)) as fh:
        scoring_settings = json.loads(fh.read())
    return scoring_settings

def write_scoring_settings(scoring_settings):
    with open("{}static/scoring_settings.json".format(prefix), "w") as fh:
        json.dump(scoring_settings, fh, indent=4)
    return

def get_scoring(which, settings):
    html = "<div id='scoring_{}'><h3>{}</h3>".format(which, which.title())
    scoring_data = get_scoring_data(which)
    #if which == "offense":
        #html += "<div>Passing Yards:<select autocomplete='off'><option>100</option><option>50</option><option selected>25</option><option>10</option><option>1</option></select> yards per point</div>"
    for j in scoring_data:
        #j["type"] = "select"
        if j["key"] not in settings:
            settings[j["key"]] = j["default"]
        html += "<div id='{}'>{}: ".format(j["key"], " ".join(j["key"].split("_")).title())
        if j["type"] == "select":
            html += "<select autocomplete='off'>"
            tag = "option"
            style = ""
        else:
            tag = "button"
            #style = "style='width: 50px;padding:5px;margin-top:-5px;'"
        for opt in j["options"]:
            html += "<{}".format(tag)
            if opt == settings[j["key"]]:
                if j["type"] == "select":
                    html += " selected"
                else:
                    html += " class='active'"            
            html += ">{}</{}>".format(opt, tag)
        if j["type"] == "select":
            html += "</select>"
        if j["key"] in ["pass_yds", "rush_yds", "rec_yds"]:
            html += "yards per point"
        html += "</div>"
    html += "</div>"
    return html


def get_scoring_html(settings):
    html = "<div style='padding-top:1.5%;'><a id='change_scoring' href='#'>Change Scoring</a></div>"
    html += "<div id='scoring'>"
    std_class = "class='active'" if settings["ppr"] == 0 else ""
    half_class = "class='active'" if settings["ppr"] == 0.5 else ""
    full_class = "class='active'" if settings["ppr"] == 1 else ""
    html +=     "<div id='ppr'><label>PPR: </label><button id='0' {}>Standard</button><button id='0.5' {}>Half</button><button id='1' {}>Full</button></div>".format(std_class, half_class, full_class)
    html +=     "<div id='main_scoring'>"
    for which in ["offense", "kicking", "defense"]:
        html += get_scoring(which, settings)
    html +=     "</div>"
    html +=     "<div id='scoring_result'>Creating and caching with specified settings</div>"
    html +=     "<div id='save_div'><button style='background-color: #00bd00;'>Save</button><button>Close</button></div>"
    html += "</div>"
    return html

def get_hide_html():
    html = "<div id='hide_div'><span style='font-weight:bold;'>Hide</span>"
    for pos in ["QB", "RB", "WR", "TE", "K", "DEF"]:
        html += "<span id='{}_hide'>{}: <input type='checkbox' /></span>".format(pos, pos)
    html += "</div>"
    return html

def decode_session(session_id):
    session_id.replace("%2C", ",")
    session_id.replace("%2F", "/")
    session_id.replace("%3F", "?")
    session_id.replace("%3A", ":")
    session_id.replace("%40", "@")
    session_id.replace("%26", "&")
    session_id.replace("%3D", "=")
    session_id.replace("%2B", "+")
    session_id.replace("%24", "$")
    session_id.replace("%23", "#")
    return session_id

def unix_time_sec(dt):
    return (dt - epoch).total_seconds()

@defense_print.route('/defense')
def defense_route():
    session_id = request.args.get("session_id")
    scoring_settings = read_scoring_settings()    

    filename = "click_html.html"
    if session_id:
        session_id = decode_session(session_id)
    
    if session_id and session_id in scoring_settings:
        settings = init_settings(scoring_settings[session_id])
        filename = scoring_settings[session_id]
    else:
        settings = default_settings()

    #print(get_settings_filename(settings))
    #ranks = profootballreference.get_ranks(7, settings)
    #opp, tot = profootballreference.position_vs_opponent_stats("ari", "DEF", ranks, settings)
    #print(opp)

    ranks_html, teams = get_ranks_html(settings)
    scoring_html = get_scoring_html(settings)
    hide_html = get_hide_html()
    settings_string = json.dumps(settings)
    color_html = ""
    click_html = ""

    with open("{}views/{}".format(prefix, filename)) as fh:
        click_html = fh.read()
    click_html = get_team_html(teams, settings)
    with open("{}views/{}".format(prefix, filename), "w") as fh:
       fh.write(click_html)
    
    return render_template("defense.html", table_html=ranks_html, color_html=color_html, click_html=click_html, scoring_html=scoring_html, hide_html=hide_html, settings_string=settings_string)


@defense_print.route('/defense', methods=["POST"])
def defense_post_route():
    settings = request.args.get("settings")    
    session_id = request.args.get("session_id")
    scoring_settings = read_scoring_settings()
    if not settings:
        return jsonify(error=1)
    elif not session_id:
        session_id = b64encode(os.urandom(64)).decode('utf-8')
        if session_id in scoring_settings:
            session_id = b64encode(os.urandom(64)).decode('utf-8')
    settings = json.loads(settings)
    settings["35+_points_allowed"] = settings["35 _points_allowed"]
    settings["field_goal_50+"] = settings["field_goal_50 "]
    del settings["35 _points_allowed"]
    del settings["field_goal_50 "]

    filename = get_settings_filename(settings)
    scoring_settings[session_id] = filename
    write_scoring_settings(scoring_settings)

    # click_html is already created. redirect to home page with session_id
    if os.path.exists("{}views/{}".format(prefix, filename)):
        return jsonify(success=1, session_id=session_id)
        #return redirect("/defense?session_id={}".format(session_id))
    # need to make click_html
    ranks_html, teams = get_ranks_html(settings)
    click_html = get_team_html(teams, settings)
    with open("{}views/{}".format(prefix, filename), "w") as fh:
       fh.write(click_html)
    return jsonify(success=1, session_id=session_id)
    #return redirect("/defense?session_id={}".format(session_id))
