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
if os.path.exists("/home/zhecht/fantasy"):
    # if on linux aka prod
    prefix = "/home/zhecht/fantasy/"

# goes from green -> yellow -> orange -> red
CURR_WEEK = 8
team_trans = {"rav": "bal", "htx": "hou", "oti": "ten", "sdg": "lac", "ram": "lar", "clt": "ind", "crd": "ari"}
display_team_trans = {"rav": "bal", "htx": "hou", "oti": "ten", "sdg": "lac", "ram": "lar", "clt": "ind", "crd": "ari", "gnb": "gb", "kan": "kc", "nwe": "ne", "rai": "lv", "sfo": "sf", "tam": "tb", "nor": "no"}

SORTED_TEAMS = ['ari', 'atl', 'bal', 'buf', 'car', 'chi', 'cin', 'cle', 'dal', 'den', 'det', 'gnb', 'hou', 'ind', 'jax', 'kan', 'lac', 'lar', 'rai', 'mia', 'min', 'nor', 'nwe', 'nyg', 'nyj', 'phi', 'pit', 'sea', 'sfo', 'tam', 'ten', 'was']

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

def get_ranks_html(settings, over_expected, curr_week=CURR_WEEK):
    ranks, defense_tot = profootballreference.get_ranks(curr_week, settings,over_expected)
    get_ranks_colors(32)

    scoring = settings["ppr"]
    defense_ranks = {}
    html = "<table id='ppg_by_pos'>"
    title = f"Fantasy Points Allowed Per Game [Sorted by Pos] ({scoring} PPR)"
    if over_expected:
        title = f"Fantasy Points Allowed Per Game Vs. Projected [Sorted by Pos] ({scoring} PPR)"
    html += f"<tr><th colspan='12'>{title}</th></tr>"
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
            val = arr[f"{pos}_ppg"]
            if over_expected:
                val = str(val)+"%"
            team_dis = display_team_trans[arr["team"]] if arr["team"] in display_team_trans else display_team
            html += "<td class='clickable {}_td'>{}</td><td id='{}_{}' class='clickable {}_td' {}>{}</td>".format(pos, team_dis.upper(), display_team, pos, pos, style, val)
        html += "</tr>"
    html += "</table>"
    
    #sorted_teams = sorted(defense_ranks.keys())
    sorted_teams = SORTED_TEAMS
    html += "<table id='ppg_by_team'>"
    title = f"Fantasy Points Allowed Per Game [Sorted by Team] ({scoring} PPR)"
    if over_expected:
        title = f"Fantasy Points Allowed Per Game Vs. Projected [Sorted by Team] ({scoring} PPR)"
    html += f"<tr><th colspan='8'>{title}</th></tr>"
    html += "<tr><th>Team</th><th class='QB_td'>QB</th><th class='RB_td'>RB</th><th class='WR_td'>WR</th><th class='TE_td'>TE</th><th class='K_td'>K</th><th class='DEF_td'>DEF</th><th> Opp</th></tr>".format(curr_week)
    for team in sorted_teams:
        opp_team = profootballreference.get_opponents(team)[curr_week]
        dis_team = display_team_trans[team] if team in display_team_trans else team
        html += "<tr><td>{}</td>".format(dis_team.upper())
        for pos in ["QB", "RB", "WR", "TE", "K", "DEF"]:
            r = defense_ranks[team]["{}_rank".format(pos)]
            style = get_ranks_style(r, extra="position:relative;z-index:-1;")
            span = "<span style='position:absolute;bottom:0;right:5px;font-size:10px;'>{}{}</span>".format(r, get_suffix(r))
            val = defense_ranks[team][pos]
            if over_expected:
                val = str(val)+"%"
            html += "<td class='clickable {}_td' id='{}_{}' {}>{}{}</td>".format(pos, team, pos, style, val, span)
        opp_team = display_team_trans[opp_team] if opp_team in display_team_trans else opp_team
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
def get_html(team_arg, pos, opp, over_expected):
    def_txt = "OFF" if pos == "DEF" else "DEF"
    html = "<table class='click_tables' id='{}_{}_table'>".format(team_arg, pos)
    mobile_html = "<table class='click_tables' id='{}_{}_mobile_table'>".format(team_arg, pos)
    with open(f"{prefix}static/projections/projections.json") as fh:
        projections = json.load(fh)
    colspan = 2
    if over_expected:
        colspan = 4
    team_dis = display_team_trans[team_arg] if team_arg in display_team_trans else team_arg
    if pos == "DEF":
        html += f"<tr><th class='{team_arg}' colspan='{colspan}' style='position:relative;'><span class='close_table'>X</span>DEF Vs. {team_dis.upper()} {def_txt}</th></tr>"
        mobile_html += f"<tr><th class='{team_arg}' style='position:relative;'><span class='close_table'>X</span>DEF Vs. {team_dis.upper()} {def_txt}</th></tr>"
    else:
        html += f"<tr><th class='{team_arg}' colspan='{colspan}' style='position:relative;'><span class='close_table'>X</span>{team_dis.upper()} {def_txt} Vs. {pos}</th></tr>"
        mobile_html += f"<tr><th class='{team_arg}' style='position:relative;'><span class='close_table'>X</span>{team_dis.upper()} {def_txt} Vs. {pos}</th></tr>"

    for idx, arr in enumerate(opp):
        players_html = "<table class='players_table'>"
        players_mobile_html = "<table class='players_table'>"
        players_proj_html = "<table class='players_proj_table'>"
        players_var_html = "<table class='players_var_table'>"
        team = ""
        total = 0
        proj_total = 0
        sched = profootballreference.get_opponents(arr["team"])
        wk = None
        for player_idx, p in enumerate(arr["players"]):
            m = re.match(r"wk(\d+) (.*): (.*) pts \((.*)\)", p)
            wk = int(m.group(1)) + 1
            team = m.group(2)
            name_pts = m.group(3)
            stats = m.group(4)
            pts = round(float(name_pts.split(" ")[-1]), 2)
            name = ' '.join(name_pts.split(" ")[:-1])
            if over_expected:
                key = name
                if pos == "DEF":
                    key = team
                if key in projections and f"wk{wk}" in projections[key]:
                    proj_total += projections[key][f"wk{wk}"]
                    total += pts
            else:
                total += pts
            player_id = "{}_vs_{}_{}_{}".format(team_arg, team, pos, player_idx)
            #if team in team_trans:
            #    team = team_trans[team]
            if pos == "DEF":
                var_html = f""
                if over_expected:
                    proj = 0
                    var = 0
                    if team in projections and f"wk{wk}" in projections[team]:
                        proj = projections[team][f"wk{wk}"]
                        if proj:
                            var = round(((pts / proj) - 1) * 100, 2)
                            var_html = f"Proj {proj}\tAct {pts}"
                    players_proj_html += f"<tr><td>{proj}</td></tr>"
                    players_var_html += f"<tr><td>{var}%</td></tr>"
                players_html += f"<tr><td style='width:25%;' class='{team}'>{pts} pts</td><td class='{team}'>{stats}</td></tr>"
                players_mobile_html += f"<tr><td><div class='mobile_show_wrapper'><a class='mobile_show_stats' href='#' id='{player_id}'>Show</a></div></td></tr><tr><td colspan='3' style='display: none;text-align: center;' id='{player_id}_stats'>{var_html}<br>[ {stats} ]</td></tr>"
            else:
                var_html = f""
                players_html += "<tr>"
                proj_html = ""
                if over_expected:
                    proj = 0
                    var = 0
                    if name in projections and f"wk{wk}" in projections[name]:
                        proj = projections[name][f"wk{wk}"]
                        if proj:
                            var = round(((pts / proj) - 1) * 100, 2)
                            var_html = f"Proj {proj}\tAct {pts}"
                    players_proj_html += f"<tr><td>{proj}</td></tr>"
                    proj_html = f" ({proj} proj)"
                    players_var_html += f"<tr><td>{var}%</td></tr>"
                players_html += f"<td class='{team}'>{name.title()}</td><td class='{team}'>{pts} pts{proj_html}</td><td class='{team}'>{stats}</td></tr>"
                players_mobile_html += f"<tr><td><div class='mobile_show_wrapper'>{name.title()}<a class='mobile_show_stats' href='#' id='{player_id}'>Show</a></div></td></tr><tr><td colspan='3' style='display: none;text-align: center;' id='{player_id}_stats'>{var_html}<br>[ {stats} ]</td></tr>"

        players_html += "</table>"
        players_mobile_html += "</table>"
        players_proj_html += "</table>"
        players_var_html += "</table>"
        tot = ""
        mobile_tot = ""
        if over_expected or pos not in ["QB", "DEF"]:
            tot = "{} pts".format(round(total, 2))
            mobile_tot = "{} pts".format(round(total, 2))
        if arr["players"] == "":
            if sched[idx] == "BYE":
                colspan = 2
                html += f"<tr><td class='{team_arg}' colspan='{colspan}'>wk{idx+1} BYE</td></tr>"
                mobile_html += "<tr><td>wk{} BYE</td></tr>".format(idx + 1)
            else:
                team_dis = display_team_trans[arr["opp_team"]] if arr["opp_team"] in display_team_trans else arr["opp_team"]
                html += "<tr><td>wk{} {}</td><td>-</td></tr>".format(idx + 1, team_dis.upper())
                mobile_html += "<tr><td>wk{} {}</td></tr><tr><td>-</td></tr>".format(idx + 1, team_dis.upper())
        elif over_expected:
            var_html = ""
            var = 0
            if proj_total:
                proj_total = round(proj_total, 2)
                var = round(((total / proj_total) - 1) * 100, 2)
                var = f"{var}%"
                var_html = f"<span class='negative'>{var}"
                if not var.startswith("-"):
                    var_html = f"<span class='positive'>+{var}"
                var_html += " vs. Proj</span>"
            if pos in ["DEF"]:
                var = players_var_html

            team_dis = display_team_trans[team] if team in display_team_trans else team
            html += f"<tr style='border:1px solid;'><td class='{team}' style='border:0px;'>wk{wk} {team_dis.upper()}: {tot}, {proj_total} Projected, {var_html}</td>"
            html += f"<tr><td style='padding:0;'>{players_html}</td></tr>"
            #html += f"<tr><td>{var}</td><td>{players_html}</td></tr>"
            #html += f"<td>{players_proj_html}</td>"
            mobile_html += f"<tr><td style='width: 100%;'>wk{wk} {team_dis.upper()}: {var_html}</td></tr><tr><td>{players_mobile_html}</td></tr>"
        else:
            team_dis = display_team_trans[team] if team in display_team_trans else team
            html += "<tr><td>wk{} {}{}</td><td>{}</td></tr>".format(wk, team_dis.upper(), tot, players_html)
            mobile_html += "<tr><td style='width: 100%;'>wk{} {}: {}</td></tr><tr><td>{}</td></tr>".format(wk, team_dis.upper(), mobile_tot, players_mobile_html)
    mobile_html += f"<tr><td class='{team_arg}'><button class='{team_arg}' onclick='close_table();'>Close</button></td></tr>"
    mobile_html += "</table>"
    html += f"<tr><td class='{team_arg}' colspan='2'><button class='{team_arg}' onclick='close_table();'>Close</button></td></tr>"
    html += "</table>"
    return html+mobile_html

def get_team_html(teams, settings, over_expected):
    curr_week = CURR_WEEK
    ranks = profootballreference.get_ranks(curr_week, settings, over_expected)

    html = ""
    for team in teams:
        for pos in ["QB", "RB", "WR", "TE", "K", "DEF"]:
            opp, tot = profootballreference.position_vs_opponent_stats(team, pos, ranks, settings)
            html += get_html(team, pos, opp[:curr_week], over_expected)
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

def get_variance_html(over_expected):
    style = ""
    if not over_expected:
        style = "style='display: none;'"
    html = f"<div {style} id='variance_div'>"
    html +=     "<div style='text-align: center;'><a id='variance_link' href='#'>Actual Vs. Projected Percent Explanation</a></div>"
    html +=     "<div id='variance_explanation' style='display: none'>"
    html +=         "<div>Act vs. Proj % gives us an insight into how well players perform against their projected fantasy points in a given week. We can also analyze a defense's strengths and weaknesses against certain positions.</div>"
    html +=         "<div>Take for example ATL Defense Vs QB Week 1. They played Russell Wilson who was projected 21.9 points but scored 31.78 points.</div>"
    html +=         "<div>var = ((actual / projected) - 1) * 100"
    html +=         "<br>var = ((31.78 / 21.9) - 1) * 100 = 45.11%</div>"
    html +=         "<div>This means that Russell scored 45% more fantasy points than was projected. We then add up all the projected and actual points across every week and calculate the percentage as a whole for the defense.<br>The same can be calculated for WR/RB as a whole unit. That is, the projected and actual points are added up for everyone at that position and then calculated for that week.</div>"
    html +=         "<div><button onclick='close_variance()'>Close</button></div>"
    html +=     "</div>"
    html += "</div>"
    return html

def get_scoring_html(settings, over_expected=False):
    style = ""
    if over_expected:
        style = "display:none;"
    html = f"<div style='{style}'><a id='change_scoring' href='#'>Change Scoring</a></div>"
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
    html = "<div id='hide_div'><span style='font-weight:bold;'>Hide</span><div id='checkbox_wrapper'>"
    for pos in ["QB", "RB", "WR", "TE", "K", "DEF"]:
        html += "<div id='{}_hide'><span>{}:</span><input type='checkbox' /></div>".format(pos, pos)
    html += "</div></div>"
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
    over_expected = request.args.get("over_expected")
    scoring_settings = read_scoring_settings()
    filename = "click_html.html"
    settings_arg = ""
    if session_id:
        session_id = decode_session(session_id)
    
    if session_id and session_id in scoring_settings:
        settings_arg = f"session_id={session_id}"
        settings = init_settings(scoring_settings[session_id])
        filename = scoring_settings[session_id]
    else:
        settings = default_settings()

    if over_expected:
        filename = filename.replace(".html", "_OE.html")

    #print(profootballreference.get_players_by_pos_team("rav", "RB"))
    #print(profootballreference.get_point_totals(3, settings, over_expected)[0])

    #print(get_settings_filename(settings))
    #ranks = profootballreference.get_ranks(3, settings)
    #opp, tot = profootballreference.position_vs_opponent_stats("was", "RB", ranks, settings)
    #print(opp)

    ranks_html, teams = get_ranks_html(settings, over_expected)
    scoring_html = get_scoring_html(settings, over_expected=over_expected)
    hide_html = get_hide_html()
    variance_html = get_variance_html(over_expected)
    link_html = f"<div id='link_div'><a href='/defense?over_expected=true&{settings_arg}'>View PPG Vs. Projected % Table</a></div>"
    if over_expected:
        link_html = f"<div id='link_div'><a href='/defense?{settings_arg}'>View PPG Table</a></div>"
    settings_string = json.dumps(settings)
    color_html = ""
    click_html = ""

    if not os.path.exists("{}views/{}".format(prefix, filename)):
        click_html = get_team_html(teams, settings, over_expected)
        with open("{}views/{}".format(prefix, filename), "w") as fh:
           fh.write(click_html)

    with open("{}views/{}".format(prefix, filename)) as fh:
        click_html = fh.read()
    if filename != "click_html_OE.html":
        from datetime import datetime
        last_modified = os.stat("{}views/{}".format(prefix, filename)).st_mtime
        dt = datetime.fromtimestamp(last_modified)
        today = datetime.now()
        if dt.year != today.year or dt.month != today.month or dt.day != today.day:
            click_html = get_team_html(teams, settings, over_expected)
            with open("{}views/{}".format(prefix, filename), "w") as fh:
               fh.write(click_html)

    return render_template("defense.html", table_html=ranks_html, color_html=color_html, click_html=click_html, scoring_html=scoring_html, variance_html=variance_html, link_html=link_html, hide_html=hide_html, settings_string=settings_string, over_expected=over_expected)


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
