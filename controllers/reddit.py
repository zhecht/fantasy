from flask import *
from subprocess import call
from bs4 import BeautifulSoup as BS
from sys import platform
from datetime import datetime

import json

reddit_blueprint = Blueprint('reddit', __name__, template_folder='views')

prefix = ""
if platform != "darwin":
    prefix = "/home/zhecht/fantasy/"

def readAskReddit():
	html = urllib.request.urlopen("https://reddit.com/r/AskReddit/rising")
	soup = BS(html.read().decode("utf8"), "lxml")


@reddit_blueprint.route('/reddit')
def reddit_route():
	return jsonify()
