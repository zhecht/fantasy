#from selenium import webdriver
from flask import *
from subprocess import call
from bs4 import BeautifulSoup as BS
from sys import platform
from datetime import datetime
from datetime import timedelta

import argparse
import glob
import json
import math
import operator
import os
import subprocess
import re
import time

betting_blueprint = Blueprint('betting', __name__, template_folder='views')

prefix = ""
if os.path.exists("/home/zhecht/fantasy"):
	# if on linux aka prod
	prefix = "/home/zhecht/fantasy/"
elif os.path.exists("/home/playerprops/fantasy"):
	# if on linux aka prod
	prefix = "/home/playerprops/fantasy/"

@betting_blueprint.route('/getBettingJSON')
def get_betting_route():
	sport = request.args.get("sport")
	prop = ""
	if request.args.get("prop"):
		prop = request.args.get("prop")

	if prop:
		with open(f"{prefix}static/betting/{sport}_{prop}.json") as fh:
			data = json.load(fh)
	else:
		with open(f"{prefix}static/betting/{sport}.json") as fh:
			data = json.load(fh)

	return jsonify(data)

@betting_blueprint.route('/betting')
def betting_route():
	prop = sport = date = ""
	if request.args.get("prop"):
		prop = request.args.get("prop").replace(" ", "+")
	if request.args.get("sport"):
		sport = request.args.get("sport")
	else:
		sport = "nhl"

	dt = time.ctime(os.path.getmtime(f"{prefix}static/betting/{sport}.json"))
	updated = datetime.strptime(dt, "%a %b %d %H:%M:%S %Y").strftime("%Y-%m-%d %I:%M %p")

	return render_template("betting.html", prop=prop, sport=sport, date=date, updated=updated)