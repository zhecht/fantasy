from flask import *
from lxml import etree
#from sql_helper import *
try:
  import controllers.constants as constants
  import controllers.read_rosters as read_rosters
  from controllers.oauth import *
except:
  import constants
  import read_rosters
  #from oauth import *

main = Blueprint('main', __name__, template_folder='views')


@main.route('/')
def main_route():
  #oauth = MyOAuth()

  all_teams = read_rosters.read_standings()
  return render_template("main.html", players=[], teams=all_teams)