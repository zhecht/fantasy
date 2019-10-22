
from sys import platform

import argparse
import os
import json

try:
	import controllers.read_rosters as read_rosters
except:
	import read_rosters

prefix = ""
if platform != "darwin":
	# if on linux aka prod
	prefix = "/home/zhecht/fantasy/"

def read_trade_values():
	with open("{}static/trade_value/tradevalues.json".format(prefix)) as fh:
		returned_json = json.loads(fh.read())
	return returned_json

def get_rosters_by_team():
	rosters, translations = read_rosters.read_rosters()
	rosters_by_team = {}
	for player in rosters:
		team = "team{}".format(rosters[player]["team_id"])
		if team not in rosters_by_team:
			rosters_by_team[team] = []
		rosters_by_team[team].append(player)
	return rosters_by_team

def calc_trade_val(tradevalues, players):
	val = 0
	for p in players:
		val += tradevalues[p]["half"]
	return val

if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument("-t", "--trade", help="Players to trade away seperated by comma")

	args = parser.parse_args()
	rosters_by_team = get_rosters_by_team()

	players_to_trade = []
	if args.trade:
		players_to_trade = args.trade.split(",")

	tradevalues = read_trade_values()
	val = calc_trade_val(tradevalues, players_to_trade)
	print(players_to_trade, val)
	exit()
	for i in range(1,13):
		if players_to_trade[0] in rosters_by_team["team{}".format(i)]:
			continue


