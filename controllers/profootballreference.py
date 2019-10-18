import argparse
import datetime
import glob
import json
import math
import os
import operator
import re
import time

from bs4 import BeautifulSoup as BS
from bs4 import Comment
from sys import platform
from subprocess import call
from glob import glob

try:
  import urllib2 as urllib
except:
  import urllib.request as urllib

prefix = ""
if platform != "darwin":
    # if on linux aka prod
    prefix = "/home/zhecht/fantasy/"

def merge_two_dicts(x, y):
    z = x.copy()
    z.update(y)
    return z

def get_points(key, val):
    if key in ["rush_yds", "rec_yds"]:
        return val * .1
    elif key in ["rush_td", "rec_td"]:
        return val * 6
    elif key == "pass_td":
        return val * 4
    elif key == "pass_yds":
        return val * .04
    elif key == "rec":
        return val * .5
    elif key in ["fumbles_lost", "pass_int"]:
        return val * -2
    return 0

def get_abbr(team):
    if team == "ari":
        return "crd"
    elif team == "bal":
        return "rav"
    elif team == "hou":
        return "htx"
    elif team == "ind":
        return "clt"
    elif team == "lac":
        return "sdg"
    elif team == "lar":
        return "ram"
    elif team == "oak":
        return "rai"
    elif team == "ten":
        return "oti"
    elif team == "tb":
        return "tam"
    elif team == "no":
        return "nor"
    elif team == "gb":
        return "gnb"
    elif team == "sf":
        return "sfo"
    elif team == "ne":
        return "nwe"
    return team

def calculate_aggregate_stats():
    teamlinks = {}
    with open("{}static/profootballreference/teams.json".format(prefix)) as fh:
        teamlinks = json.loads(fh.read())
    
    for team in teamlinks:
        stats = {}
        path = "{}static/profootballreference/{}".format(prefix, team.split("/")[-2])
        files = glob("{}/wk*.json".format(path))
        for f in files:
            m = re.search(r'wk(\d+).json', f)
            week = m.group(1)
            team_stats = {}
            with open(f) as fh:
                team_stats = json.loads(fh.read())

            for player in team_stats:
                if player not in stats:
                    stats[player] = {"tot": {"points": 0}}
                if "wk{}".format(week) not in stats[player]:
                    stats[player]["wk{}".format(week)] = {}

                points = 0
                for player_stats_str in team_stats[player]:
                    if player_stats_str not in stats[player]["tot"]:
                        stats[player]["tot"][player_stats_str] = 0
                    stats[player]["wk{}".format(week)][player_stats_str] = team_stats[player][player_stats_str]
                    stats[player]["tot"][player_stats_str] += team_stats[player][player_stats_str]
                    points += get_points(player_stats_str, team_stats[player][player_stats_str])
                
                stats[player]["wk{}".format(week)]["points"] = round(points, 2)
                stats[player]["tot"]["points"] += round(points, 2)
            
        with open("{}/stats.json".format(path), "w") as fh:
            json.dump(stats, fh, indent=4)

# return (in order) list of opponents
def get_opponents(team):
    team = get_abbr(team)
    schedule = {}
    with open("{}static/profootballreference/schedule.json".format(prefix)) as fh:
        schedule = json.loads(fh.read())
    opps = []
    for i in range(1, 18):
        opp_team = "BYE"
        for games in schedule[str(i)]:
            away, home = games.split(" @ ")
            if away == team:
                opp_team = home
            elif home == team:
                opp_team = away
        opps.append(opp_team)
    return opps


# read rosters and return ARRAY of players on team playing POS 
def get_players_by_pos_team(team, pos):
    roster = {}
    with open("{}static/profootballreference/{}/roster.json".format(prefix, team)) as fh:
        roster = json.loads(fh.read())
    arr = []
    for player in roster:
        if roster[player].lower() == pos.lower():
            arr.append(player)
    if team == "pit" and pos == "QB":
        arr.append("ben roethlisberger")
    elif team == "nwe" and pos == "WR":
        arr.append("antonio brown")
    return arr

def get_tot_team_games(curr_week, schedule):
    j = {}
    for i in range(1, curr_week + 1):
        games = schedule[str(i)]
        for game in games:
            t1,t2 = game.split(" @ ")
            if t1 not in j:
                j[t1] = 0
            if t2 not in j:
                j[t2] = 0
            j[t1] += 1
            j[t2] += 1
    return j

def get_point_totals(curr_week):
    teams = os.listdir("{}static/profootballreference".format(prefix))
    all_team_stats = {}
    # read all team stats into { team -> player -> [tot, wk1, wk2]}
    for team in teams:
        if team.find("json") >= 0:
            continue
        stats = {}
        with open("{}static/profootballreference/{}/stats.json".format(prefix, team)) as fh:
            stats = json.loads(fh.read())
        all_team_stats[team] = stats.copy()
    ranks = []
    for team in all_team_stats:
        pos_tot = {}
        for pos in ["RB", "WR", "TE", "QB"]:
            pos_tot[pos] = {}
            players = get_players_by_pos_team(team, pos)
            
            for player in players:
                if player not in all_team_stats[team]:                  
                    continue
                for wk in all_team_stats[team][player]: # tot, wk1, wk2
                    if wk not in pos_tot[pos]:
                        pos_tot[pos][wk] = 0
                    pos_tot[pos][wk] += all_team_stats[team][player][wk]["points"]
        j = { "team": team }
        for pos in pos_tot:
            #if "{}_tot".format(pos) not in j:
                #j["{}_tot".format(pos)] = 0
            for wk in range(1, curr_week + 1):
                if "wk{}".format(wk) not in pos_tot[pos]: # game hasn't played
                    j["{}_wk{}".format(pos, wk)] = 0
                else:
                    j["{}_wk{}".format(pos, wk)] = round(pos_tot[pos]["wk{}".format(wk)], 2)
                    #j["{}_tot".format(pos)] += pos_tot[pos]["wk{}".format(wk)]
            #j["{}_tot".format(pos)] = round(j["{}_tot".format(pos)], 2)
        ranks.append(j)
    return ranks


def read_schedule():
    with open("{}static/profootballreference/schedule.json".format(prefix)) as fh:
        j = json.loads(fh.read())
    return j

def get_defense_tot(curr_week, point_totals_dict):
    defense_tot = []
    schedule = read_schedule()
    tot_team_games = get_tot_team_games(curr_week, schedule)
    teams = os.listdir("{}static/profootballreference".format(prefix))
    for team in teams:
        if team.find("json") >= 0:
            continue
        # get opp schedule
        j = {"team": team}
        opponents = get_opponents(team)[:curr_week]
        for week, opp_team in enumerate(opponents):
            for pos in ["QB", "RB", "WR", "TE"]:
                key = "{}_wk{}".format(pos, week + 1)
                tot_key = "{}_tot".format(pos)
                if key not in j:
                    j[key] = 0
                if tot_key not in j:
                    j[tot_key] = 0
                if opp_team != "BYE":
                    j[key] += point_totals_dict[opp_team][key]
                    j[tot_key] += point_totals_dict[opp_team][key]
        for pos in ["QB", "RB", "WR", "TE"]:
            games = tot_team_games[team]
            j["{}_ppg".format(pos)] = round(j["{}_tot".format(pos)] / games, 2)
        defense_tot.append(j)
    return defense_tot

# get rankns of teeams sorted by highest fantasy points scored
def get_ranks(curr_week):
    ranks = {}
    point_totals = get_point_totals(curr_week)
    for pos in ["RB", "WR", "TE", "QB"]:
        for week in range(1, curr_week + 1):
            key = "{}_wk{}".format(pos, week)
            # storred like RB_wk3, etc
            sorted_ranks = sorted(point_totals, key=operator.itemgetter(key), reverse=True)
            for idx, arr in enumerate(sorted_ranks):
                if arr["team"] not in ranks:
                    ranks[arr["team"]] = {"RB": {}, "WR": {}, "TE": {}, "QB": {}}
                ranks[arr["team"]][pos]["wk{}".format(week)] = idx + 1

    # total opponent's numbers for DEFENSE outlooks
    point_totals_dict = {}
    for arr in point_totals:
        point_totals_dict[arr["team"]] = arr.copy()
    defense_tot = get_defense_tot(curr_week, point_totals_dict)

    for pos in ["RB", "WR", "TE", "QB"]:
        sorted_ranks = sorted(defense_tot, key=operator.itemgetter("{}_tot".format(pos)), reverse=True)
        for idx, arr in enumerate(sorted_ranks):
            ranks[arr["team"]][pos]["tot"] = idx + 1

    return ranks, defense_tot


def get_pretty_stats(stats, pos):
    #s = "{} PTS - {}".format(stats["points"], player.title())
    s = ""
    pos = pos.upper()
    if pos == "QB":
        s += "{}/{} {} Pass Yds".format(stats["pass_cmp"], stats["pass_att"], stats["pass_yds"])
        if stats["pass_td"]:
            s += ", {} Pass TD".format(stats["pass_td"])
        if stats["pass_int"]:
            s += ", {} Int".format(stats["pass_int"])
    elif pos in ["WR", "TE"]:
        s = "{}/{} {} Rec Yds".format(stats["rec"], stats["targets"], stats["rec_yds"])
        if stats["rec_td"]:
            s += " {} Rec TD".format(stats["rec_td"])
    else: # RB
        s += "{} Rush Yds".format(stats["rush_yds"])
        if stats["rush_td"]:
            s += ", {} Rush TD".format(stats["rush_td"])
        if stats["rec"]:
            s += ", {} Rec, {} Rec Yds".format(stats["rec"], stats["rec_yds"])
        if stats["rec_td"]:
            s += ", {} Rec TD".format(stats["rec_td"])
    return s

team_trans = {"rav": "bal", "htx": "hou", "oti": "ten", "sdg": "lac", "ram": "lar", "rai": "oak", "clt": "ind", "crd": "ari"}

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

# Given a team, show stats from other players at the same pos 
def position_vs_opponent_stats(team, pos, ranks):
    opp_stats = []
    tot_stats = {"points": 0, "stats": {}, "title": "TOTAL vs. {}".format(pos.upper())}
    team = get_abbr(team)
    team_schedule = get_opponents(team)
    for idx, opp_team in enumerate(team_schedule):
        if opp_team == "BYE":
            continue
        week = idx + 1
        path = "{}static/profootballreference/{}".format(prefix, opp_team)
        team_stats = {}
        with open("{}/stats.json".format(path)) as fh:
            team_stats = json.loads(fh.read())
        players_arr = get_players_by_pos_team(opp_team, pos)
        display_team = team_trans[team] if team in team_trans else team
        display_opp_team = team_trans[opp_team] if opp_team in team_trans else opp_team
        j = {
            "title": "<i style='text-decoration:underline;'>{} vs. {} {}</i>".format(
                display_team.upper(),
                display_opp_team.upper(),
                pos.upper()
            ),
            "text": "",
            "rank": "",
            "points": 0.0,
            "players": "",
            "stats": None
        }
        total_stats = {}
        player_txt = []
        for player in players_arr:
            if player not in team_stats or "wk{}".format(week) not in team_stats[player]:
                continue
            week_stats = team_stats[player]["wk{}".format(week)]
            
            for s in week_stats:
                if s not in total_stats:
                    total_stats[s] = 0
                if s == "points":
                    player_txt.append("wk{} {}: {} {} pts ({})".format(idx, opp_team, player, week_stats[s],get_pretty_stats(week_stats, pos)))
                    #print("wk{} {}: {} {} pts ({})".format(
                    #   idx, opp_team, player, week_stats[s],get_pretty_stats(week_stats, pos))
                    #)
                total_stats[s] += week_stats[s]
        try:
            
            if 0:
                j["rank"] = "{} points allowed <span>{}{} highest</span>".format(
                    #total_stats[pos.upper()]["points"],
                    total_stats["points"],              
                    ranks[opp_team][pos.upper()]["wk{}".format(week)],
                    get_suffix(ranks[opp_team][pos.upper()]["wk{}".format(week)])
                )
            j["team"] = team
            j["opp_team"] = opp_team
            j["stats"] = total_stats 
            j["text"] = get_pretty_stats(total_stats, pos)
            j["points"] = round(total_stats["points"], 2)
            j["players"] = player_txt

            # TOT
            tot_stats["points"] += j["points"]
            for key in total_stats:
                if key not in tot_stats["stats"]:
                    tot_stats["stats"][key] = 0
                tot_stats["stats"][key] += total_stats[key]
        except:
            pass

        opp_stats.append(j)
    tot_stats["text"] = get_pretty_stats(tot_stats["stats"], pos)
    tot_stats["rank"] = "{} points allowed <span>{}{} highest</span>".format(
        round(tot_stats["points"], 2),
        0,0)
    #   ranks[opp_team][pos.upper()]["tot"],
    #   get_suffix(ranks[opp_team][pos.upper()]["tot"])
    #)
    return opp_stats, tot_stats

def get_total_ranks(curr_week):
    ranks, defense_tot = get_ranks(curr_week)

    print("RANK|RB|WR|TE|QB")
    print(":--|:--|:--|:--|:--")
    for idx in range(1, 33):
        s = "**{}**".format(idx)
        for pos in ["RB", "WR", "TE", "QB"]:
            sorted_ranks = sorted(defense_tot, key=operator.itemgetter("{}_ppg".format(pos)), reverse=False)
            display_team = sorted_ranks[idx - 1]["team"]
            if display_team in team_trans:
                display_team = team_trans[display_team]
            tot = round(sorted_ranks[idx - 1]["{}_tot".format(pos)], 2)
            s += "|{} {} PPG".format(display_team, sorted_ranks[idx - 1]["{}_ppg".format(pos)])
        print(s)

def write_team_links():
    url = "https://www.pro-football-reference.com/teams/"
    soup = BS(urllib.urlopen(url).read(), "lxml")
    rows = soup.find("table", id="teams_active").find_all("tr")[2:]
    j = {}
    for tr in rows:
        try:
            link = tr.find("th").find("a").get("href")
            j[link] = 1
        except:
            pass
    with open("{}static/profootballreference/teams.json".format(prefix), "w") as fh:
        json.dump(j, fh, indent=4)

def write_boxscore_links():
    teamlinks = {}
    with open("{}static/profootballreference/teams.json".format(prefix)) as fh:
        teamlinks = json.loads(fh.read())

    for team in teamlinks:
        path = "{}static/profootballreference/{}".format(prefix, team.split("/")[-2])
        if not os.path.exists(path):
            call(["mkdir", "-p", path])
        url = "https://www.pro-football-reference.com{}/2019/gamelog".format(team)
        soup = BS(urllib.urlopen(url).read(), "lxml")
        boxscore_links = {}
        for i in range(16):
            row = soup.find("tr", id="gamelog2019.{}".format(i + 1))
            if row:
                link = row.find("a")
                if link.text == "preview":
                    break
                boxscore_links[link.get("href")] = i + 1
        with open("{}/boxscores.json".format(path), "w") as fh:
            json.dump(boxscore_links, fh, indent=4)

def write_team_rosters():
    teamlinks = {}
    with open("{}static/profootballreference/teams.json".format(prefix)) as fh:
        teamlinks = json.loads(fh.read())

    for team in teamlinks:
        roster = {}
        path = "{}static/profootballreference/{}".format(prefix, team.split("/")[-2])

        if not os.path.exists(path):
            os.mkdir(path)
        url = "https://www.pro-football-reference.com{}/2019_roster.htm".format(team)
        outfile = "{}/roster.html".format(path)
        call(["curl", "-k", url, "-o", outfile])

        # for some reason, the real HTML is commented out?
        soup = BS(open(outfile).read(), "lxml")
        rows = soup.find("table", id="starters").find_all("tr")[1:]
        for tr in rows:
            tds = tr.find_all("td")
            name = tds[0].text.lower().replace("'", "").replace(".", "")
            pos = tr.find("th").text
            if name.find("starters") == -1:
                roster[name] = pos

        soup = BS(open(outfile).read(), "lxml")
        if soup.find("div", id="all_games_played_team") is None:
            continue
        children = soup.find("div", id="all_games_played_team").children
        html = None
        for c in children:
            if isinstance(c, Comment):
                html = c
        os.remove(outfile)

        soup = BS(html, "lxml")
        rows = soup.find("table", id="games_played_team").find_all("tr")[1:]
        for tr in rows:
            tds = tr.find_all("td")
            name = tds[0].text.lower().replace("'", "").replace(".", "")
            pos = tds[2].text
            roster[name] = pos
        if team == "rai":
            roster["darren waller"] = "TE"
        elif team == "det":
            roster["ty johnson"] = "RB"
            roster["jd mckissic"] = "RB"
        with open("{}/roster.json".format(path), "w") as fh:
            json.dump(roster, fh, indent=4)

def get_indexes(header_row):
    indexes = {}
    for idx, th in enumerate(header_row):
        # get indexes
        indexes[th.get("data-stat")] = idx
    return indexes

def write_schedule():
    url = "https://www.pro-football-reference.com/years/2019/games.htm"
    soup = BS(urllib.urlopen(url).read(), "lxml")
    rows = soup.find("table", id="games").find_all("tr")[1:] # skip header row
    schedule = {}
    for tr in rows:
        if tr.get("class") and "thead" in tr.get("class"):
            continue
        week = int(tr.find("th").text)
        if week not in schedule:
            schedule[week] = []
        winner = tr.find_all("td")[3].find("a").get("href").split("/")[-2]
        location = tr.find_all("td")[4].text
        loser = tr.find_all("td")[5].find("a").get("href").split("/")[-2]
        s = "{} @ {}".format(loser, winner)
        if location == "@":
            s = "{} @ {}".format(winner, loser)
        schedule[week].append(s)
    with open("{}static/profootballreference/schedule.json".format(prefix), "w") as fh:
        json.dump(schedule, fh, indent=4)

def write_boxscore_stats():
    teamlinks = {}
    with open("{}static/profootballreference/teams.json".format(prefix)) as fh:
        teamlinks = json.loads(fh.read())

    for link in teamlinks:
        team = link.split("/")[-2]
        teampath = "{}static/profootballreference/{}".format(prefix, team)
        boxscorelinks = {}
        with open("{}/boxscores.json".format(teampath)) as fh:
            boxscorelinks = json.loads(fh.read())
        for boxlink in boxscorelinks:
            #print(team, boxlink)
            url = "https://www.pro-football-reference.com{}#all_team_stats".format(boxlink)
            outfile = "{}/wk{}.html".format(teampath, boxscorelinks[boxlink])
            call(["curl", "-k", url, "-o", outfile])

            # for some reason, the real HTML is commented out?
            soup = BS(open(outfile).read(), "lxml")
            if soup.find("div", id="all_player_offense") is None:
                continue
            children = soup.find("div", id="all_player_offense").children
            html = None
            for c in children:
                if isinstance(c, Comment):
                    html = c
            soup = BS(html, "lxml")
            rows = soup.find("table", id="player_offense").find_all("tr")
            stats = {}
            for tr in rows[2:]:
                classes = tr.get("class")
                if classes and "thead" in classes:
                    continue
                name = tr.find("th").text.lower().replace("'", "").replace(".", "")
                data = tr.find_all("td")
                ck_team = get_abbr(data[0].text.lower()) # might have different abbr
                
                if team == ck_team:
                    stats[name] = {}
                    for td in data[1:]: # skip team
                        try:
                            if td.get("data-stat") == "pass_rating":
                                stats[name][td.get("data-stat")] = float(td.text)
                            else:   
                                stats[name][td.get("data-stat")] = int(td.text)
                        except:
                            stats[name][td.get("data-stat")] = 0

            with open("{}/wk{}.json".format(teampath, boxscorelinks[boxlink]), "w") as fh:
                json.dump(stats, fh, indent=4)
            os.remove(outfile)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--cron", action="store_true", help="Start Cron Job")
    parser.add_argument("-r", "--ranks", action="store_true", help="Get Ranks")
    parser.add_argument("-schedule", "--schedule", help="Print Schedule", action="store_true")
    parser.add_argument("-s", "--start", help="Start Week", type=int)
    parser.add_argument("-e", "--end", help="End Week", type=int)

    args = parser.parse_args()
    curr_week = 6

    if args.start:
        curr_week = args.start
    
    if args.schedule:
        schedule = read_schedule()
        print(schedule[str(curr_week)])
    elif args.ranks:
        get_total_ranks(curr_week)
        #ranks = get_ranks(3)
        #opp1 = position_vs_opponent_stats("nwe", "RB", ranks)
        #print(opp1)

    elif args.cron:
        pass
        # only needs to be run once in a while
        write_schedule()
        write_team_rosters()
        write_team_links()
        write_boxscore_links()      
        write_boxscore_stats()
        calculate_aggregate_stats()
