#from selenium import webdriver
from flask import *
from subprocess import call
from bs4 import BeautifulSoup as BS
from sys import platform

#from selenium.webdriver.firefox.options import Options

import json
import math
import operator
import os
import subprocess
import re

try:
    import controllers.profootballreference as profootballreference
    import controllers.compare as compare
except:
    import profootballreference
    import compare

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

def get_ranks_html(curr_week=6):
    ranks, defense_tot = profootballreference.get_ranks(curr_week)
    get_ranks_colors(32)

    defense_ranks = {}
    html = "<table id='ppg_by_pos'>"
    html += "<tr><th colspan='8'>Points Allowed Per Game Per Position (0.5 PPR)</th></tr>"
    html += "<tr><th>Team</th><th>QB</th><th>Team</th><th>RB</th><th>Team</th><th>WR</th><th>Team</th><th>TE</th></tr>"
    # sorted by pos
    for idx in range(32):
        html += "<tr>"
        style = get_ranks_style(idx + 1)
        for pos in ["QB", "RB", "WR", "TE"]:
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
            
            html += "<td class='clickable'>{}</td><td id='{}_{}' class='clickable' {}>{}</td>".format(display_team.upper(), display_team, pos, style, arr["{}_ppg".format(pos)])
        html += "</tr>"
    html += "</table>"
    
    sorted_teams = sorted(defense_ranks.keys())
    html += "<table id='ppg_by_team'>"
    html += "<tr><th colspan='5'>Points Allowed Per Game (0.5 PPR)</th></tr>"
    html += "<tr><th>Team</th><th>QB</th><th>RB</th><th>WR</th><th>TE</th></tr>"
    for team in sorted_teams:
        html += "<tr><td>{}</td>".format(team.upper())
        for pos in ["QB", "RB", "WR", "TE"]:
            r = defense_ranks[team]["{}_rank".format(pos)]
            style = get_ranks_style(r, extra="position:relative;z-index:-1;")
            span = "<span style='position:absolute;bottom:0;right:5px;font-size:10px;'>{}{}</span>".format(r, get_suffix(r))
            html += "<td class='clickable' id='{}_{}' {}>{}{}</td>".format(team, pos, style, defense_ranks[team][pos], span)
        html += "</tr>"
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
    html = "<table class='click_tables' id='{}_{}_table'>".format(team_arg, pos)
    html += "<tr><th colspan='2'>{} DEF Vs. {}</th></tr>".format(team_arg.upper(), pos)
    for idx, arr in enumerate(opp):
        players_html = "<table class='players_table'>"
        team = ""
        total = 0
        sched = profootballreference.get_opponents(arr["team"])
        for p in arr["players"]:
            m = re.match(r"wk(\d+) (.*): (.*) pts \((.*)\)", p)
            wk = int(m.group(1)) + 1
            team = m.group(2)
            name_pts = m.group(3)
            stats = m.group(4)
            pts = float(name_pts.split(" ")[-1])
            total += pts
            name = ' '.join(name_pts.split(" ")[:-1])
            if team in team_trans:
                team = team_trans[team]
            players_html += "<tr><td style='width: 90px;padding-left:10px;'>{} pts</td><td style='width: 175px;'>{}</td><td>{}</td></tr>".format(pts, name.title(), stats)
        players_html += "</table>"
        tot = ""
        if pos != "QB":
            tot = "\n{} pts".format(round(total, 2))
        
        if arr["players"] == "":
            if sched[idx] == "BYE":
                html += "<tr><td style='width:100px;'>wk{} BYE</td><td></td></tr>".format(idx + 1)
            else:
                html += "<tr><td style='width:100px;'>wk{} {}</td><td>-</td></tr>".format(idx + 1, arr["opp_team"].upper())
        else:
            html += "<tr><td style='width:100px;'>wk{} {}{}</td><td>{}</td></tr>".format(wk, team.upper(), tot, players_html)

    html += "</table>"
    return html

def get_team_html(teams):
    curr_week = 6
    ranks = profootballreference.get_ranks(curr_week)
    html = ""
    #return html
    for team in teams:
        for pos in ["QB", "RB", "WR", "TE"]:
            opp, tot = profootballreference.position_vs_opponent_stats(team, pos, ranks)
            html += get_html(team, pos, opp[:curr_week])
    #print(html)
    return html


@defense_print.route('/defense')
def defense_route():
    ranks_html, teams = get_ranks_html()
    #color_html = get_color_html()
    color_html = ''
    click_html = ""
    with open("{}views/click_html.html".format(prefix)) as fh:
        click_html = fh.read()
    #click_html = get_team_html(teams)
    #with open("views/click_html.html", "w") as fh:
    #   fh.write(click_html)
    return render_template("defense.html", table_html=ranks_html, color_html=color_html, click_html=click_html)
