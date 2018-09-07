import sys
from subprocess import call

try:
  curr_week = int(sys.argv[1])
except:
  curr_week = 2


call(["python", "controllers/read_rosters.py", "-c"])
call(["python3", "controllers/read_twitter.py", "-c"])
call(["python", "controllers/stats.py", "-c", "-s", str(curr_week)])
call(["python", "controllers/espn_stats.py", "-c", "-s", str(curr_week)])
call(["python", "controllers/fantasypros_stats.py", "-c", "-s", str(curr_week)])
call(["python", "controllers/snap_stats.py"])