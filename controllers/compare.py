#from selenium import webdriver
from flask import *
from subprocess import call
from bs4 import BeautifulSoup as BS
from sys import platform

#from selenium.webdriver.firefox.options import Options

import json
import operator
import os
import subprocess
import cv2

try:
	import controllers.borischen as borischen
	import controllers.redzone as redzone
	import controllers.airyards as airyards
	import controllers.nextgen as nextgen
	import controllers.profootballreference as profootballreference
except:
	import redzone
	import airyards
	import borischen
	import nextgen
	import profootballreference

try:
	import urllib2 as urllib
except:
	import urllib.request as urllib

compare_print = Blueprint('compare', __name__, template_folder='views')


prefix = ""
if platform != "darwin":
	# if on linux aka prod
	prefix = "/home/zhecht/fantasy/"

def merge_two_dicts(x, y):
	z = x.copy()
	z.update(y)
	return z

def get_fp_name(name):
	if len(name.split(" ")) == 3:
		without_extra = name.split(" ")[:-1]
		return '-'.join(without_extra)
	name = name.replace(" ", "-")
	if name == "tj-hockenson":
		return "t.j.-hockenson"
	return name

def create_fp_pic(player1, player2):
	path = "{}static/screenshots/{}_{}".format(prefix, player1.replace(" ", "_"), player2.replace(" ", "_"))
	if os.path.exists(path+"-full.png"):
		return path
	url = "https://www.fantasypros.com/nfl/start/{}-{}.php?scoring=HALF".format(get_fp_name(player1), get_fp_name(player2))
	cmd = ["webkit2png", "-F", "-o", path, url]

	subprocess.run(cmd)
	img = cv2.imread("{}-full.png".format(path))

	# (left, top, right, bottom)
	#img = img.crop((250, 1200, 1200, 2200)).save("{}-full.png".format(path))
	img_crop = img[1200:2200, 250:1200]
	cv2.imwrite("{}-full.png".format(path), img_crop)
	return path

def get_fp_html(player1, player2):
	url = "https://www.fantasypros.com/nfl/start/{}-{}.php?scoring=HALF".format(
		get_fp_name(player1), get_fp_name(player2)
	)
	call(["curl", "-k", url, "-o", "{}static/fantasypros/{}_{}.html".format(prefix, player1.replace(" ", "_"), player2.replace(" ", "_"))])
	html = open("{}static/fantasypros/{}_{}.html".format(prefix, player1.replace(" ", "_"), player2.replace(" ", "_")))
	soup = BS(html.read(), "lxml")
	table = soup.find("table")
	html = "<table id='fp_table' class='table full-width table-wsis' cellspacing='0' cellpadding='0' border='0'>"
	rows = table.find_all("tr")[:13]
	for idx, tr in enumerate(rows):
		if idx < 3 or idx >= 7:
			html += str(tr)
	html += "</table>"
	return html
	

def get_airyards_html(airyards1, airyards2):
	html = "<h4 style='margin-top: 1%;'><a href='http://airyards.com/tables.html' target='_blank'>Airyards.com</a></h4>"
	html += "<table id='airyards_table'>"
	html += "<tr>"
	for stat in ["", "rec", "targets", "tgt_share", "yac", "td", "adot", "air_yards", "wopr"]:
		html += "<th>{}</th>".format(stat)
	html += "</tr>"
	for data in [airyards1, airyards2]:
		html += "<tr><td>{}</td>".format(data["full_name"])
		for stat in ["rec", "targets", "tgt_share", "yac", "td", "adot", "air_yards", "wopr"]:
			html += "<td>{}</td>".format(data[stat])
		html += "</tr>"
	html += "</table>"
	return html

def get_redzone_html(redzone, player1, player2):
	html = "<h4><a href='http://subscribers.footballguys.com/teams/teampage-atl-3.php' target='_blank'>subscribers.Footballguys.com</a></h4>"
	html += "<table id='redzone_table'>"
	html += "<tr><th></th><th>Snap %</th><th>RZ Looks</th><th>RZ Looks Share</th><th>TGTS</th><th>Target Share</th></tr>"
	for p in [player1, player2]:
		html += "<tr><td>{}</td>".format(p)
		data = redzone[p]
		html += "<td>{}% ({})</td><td>{} ({})</td><td>{}% ({})</td><td>{} ({})</td><td>{}% ({})</td>".format(
			data["snaps"], data["snaps_trend"], data["total_looks"], data["looks_trend"],
			data["looks_share"], data["looks_share_trend"], data["total_targets"], data["target_trend"], data["target_share"], data["target_share_trend"]
		)
		html += "</tr>"
	html += "</table>"
	return html

def fill_empty(nextgen, player1, player2):
	if player1 not in nextgen:
		nextgen[player1] = nextgen[player2].copy()
		for stat in nextgen[player1]:
			if stat not in ["team", "pos"]:
				nextgen[player1][stat] = 0
	elif player2 not in nextgen:
		nextgen[player2] = nextgen[player1].copy()
		for stat in nextgen[player2]:
			if stat not in ["team", "pos"]:
				nextgen[player2][stat] = 0

def get_nextgen_html(nextgen, player1, player2):
	fill_empty(nextgen, player1, player2)
	headers = nextgen[player1]
	pos1 = nextgen[player1]["pos"]
	pos2 = nextgen[player2]["pos"]
	
	html = "<h4><a href='https://nextgenstats.nfl.com/stats/receiving' target='_blank'>NextGenStats.nfl.com</a></h4>"
	html += "<table id='nextgen_table'>"
	if pos1 == pos2 or (pos1 in ["WR", "TE"] and pos2 in ["WR", "TE"]):
		html += "<tr><th></th>"
		for stat in headers:
			if stat in ["pos", "team", "cush", "ctch%", "xyac/r", "+/-", "rec", "tar", "tay"]:
				continue
			if stat == "tay%":
				stat = "team airyard share"
			html += "<th>{}</th>".format(stat)
		html += "</tr>"
		for p in [player1, player2]:
			data = nextgen[p]
			html += "<tr><td>{}</td>".format(p)
			for stat in headers:
				if stat in ["pos", "team", "cush", "ctch%", "xyac/r", "+/-", "rec", "tar", "tay"]:
					continue
				html += "<td>{}</td>".format(data[stat])
			html += "</tr>"
	html += "</table>"
	return html

def get_borischen_html(tiers, airyards_j, player1, player2):
	player1_tier = tiers[player1] if player1 in tiers else None
	player2_tier = tiers[player2] if player2 in tiers else None
	html = "<div id='borischen_table'>"
	html += "<h4><a href='http://www.borischen.co/p/half-05-5-ppr-wide-receiver-tier.html' target='_blank'>Borischen.co</a></h4>"
	html += "<span>{}: Tier {} -- {}: Tier {}</span>".format(player1.title(), player1_tier, player2.title(), player2_tier)
	html += "<span></span>".format()
	if airyards_j[player1]["pos"].lower() == 'rb':
		html += "<img src='{}/static/borischen/rb.png' />".format(prefix)
	elif airyards_j[player1]["pos"].lower() == 'wr':
		html += "<img src='{}/static/borischen/wr.png' />".format(prefix)
	elif airyards_j[player1]["pos"].lower() == 'te':
		html += "<img src='{}/static/borischen/te.png' />".format(prefix)
	elif airyards_j[player1]["pos"].lower() == 'qb':
		html += "<img src='{}/static/borischen/qb.png' />".format(prefix)

	#html += ""<airyards[player1]["pos"]
	#airyards[player2]["pos"]
	html += "</div>"
	return html

def format_opp(opp):
	return "<table><tr><th>{}</th></tr><tr><td>{}</td></tr><tr><td>{}</td></tr></table>".format(
		opp["title"],
		opp["rank"],
		opp["text"]
	)

def get_opp_html(nextgen_stats, player1, player2, curr_week):
	team1 = nextgen_stats[player1]["team"].lower()
	team2 = nextgen_stats[player2]["team"].lower()
	# get current opp (not -1 bc we want next weeks opp)
	team1 = profootballreference.get_opponents(team1)[curr_week]
	team2 = profootballreference.get_opponents(team2)[curr_week]

	pos1 = nextgen_stats[player1]["pos"].lower()
	pos2 = nextgen_stats[player2]["pos"].lower()
	ranks = profootballreference.get_ranks(curr_week)
	opp1, tot1 = profootballreference.position_vs_opponent_stats(team1, pos1, ranks)
	opp2, tot2 = profootballreference.position_vs_opponent_stats(team2, pos2, ranks)
	html = "<h4>Opponent Stats</h4><table id='opponent_table'>"
	html += "<tr><th>Wk</th><th>{} Wk{} opp: {}</th><th>{} Wk{} opp: {}</th></tr>".format(player1.title(), curr_week + 1, team1.upper(), player2.title(), curr_week + 1, team2.upper())

	html += "<tr><td></td><td>{}</td><td>{}</td></tr>".format(format_opp(tot1), format_opp(tot2))
	for i in range(curr_week, 0, -1):
		html += "<tr><td>{}</td><td>{}</td><td>{}</td></tr>".format(i, format_opp(opp1[i - 1]), format_opp(opp2[i - 1]))
	html += "</table>"
	#print(team1, pos1, opp1)
	#print(team2, pos2, opp2)
	return html

@compare_print.route('/compare/<player1>/<player2>')
def compare_route(player1, player2):
	player1 = player1.lower().replace("'", "").replace(".", "")
	player2 = player2.lower().replace("'", "").replace(".", "")
	
	#path = ""
	#path = create_fp_pic(player1, player2)
	fp_html = get_fp_html(player1, player2)
	curr_week = 4

	#print("tiers", player1_tier, player2_tier)

	# subscribers.footballguys (last arg for is_ui)
	redzone_wr_trends = redzone.get_redzone_trends([], curr_week - 1, "WR/TE", True)
	redzone_rb_trends = redzone.get_redzone_trends([], curr_week - 1, "RB", True)
	redzone_trends = merge_two_dicts(redzone_wr_trends, redzone_rb_trends)
	redzone_html = get_redzone_html(redzone_trends, player1, player2)
	#print(redzone_trends)

	# airyards
	airyards_hash = airyards.read_airyards_trends(curr_week - 1)
	airyards_html = get_airyards_html(airyards_hash[player1], airyards_hash[player2])

	# borischen
	tiers = borischen.read_borischen_tiers(curr_week - 1)	
	borischen_html = get_borischen_html(tiers, airyards_hash, player1, player2)

	# nfl next gen
	nextgen_stats = nextgen.read_nextgen_trends(curr_week - 1)
	nextgen_html = get_nextgen_html(nextgen_stats, player1, player2)

	# Opp data	
	opp_html = get_opp_html(nextgen_stats, player1, player2, curr_week - 1)
	

	return render_template("compare.html", name1=player1.title(), name2=player2.title(), airyards_html=airyards_html, nextgen_html=nextgen_html, redzone_html=redzone_html, borischen_html=borischen_html, fp_html=fp_html, opp_html=opp_html)

#compare_route('miles sanders', 'sony michel')