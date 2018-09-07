#import MySQLdb
try:
  import controllers.constants as constants
except:
  import constants

import pymysql

def makeDB():
  db = pymysql.connect(
    host = constants.HOST_CONST,
    user = constants.USER_CONST,
    passwd = constants.PASSWRD_CONST,
    db = constants.DB_CONST
  )
  return db

def makeCursor():
  return makeDB().cursor()

def getPlayerID(name, team):
  cursor = makeCursor()
  cursor.execute("SELECT id FROM Player WHERE name='%s' AND team='%s'" % (name,team.upper(),))
  return cursor.fetchone()

def getName(pid):
  if pid == None:
    return None
  cursor = makeCursor()
  cursor.execute("SELECT name FROM Player WHERE id=%s" % (pid,))
  return cursor.fetchone()

def getProjection(pid, curr_week):
  col = 'y'+str(curr_week)
  col2 = 'e'+str(curr_week)
  cursor = makeCursor()
  
  cursor.execute("SELECT %s,%s FROM Projections WHERE pid=%s" % (col,col2,pid,))

  return cursor.fetchall()

def getWeeklyESPN(pid, curr_week):
  cursor = makeCursor()
  cursor.execute("SELECT * FROM Projections WHERE pid=%s" % (pid,))
  projections = cursor.fetchall()[0]
  comma = ","
  return comma.join(projections[17:17+curr_week])

def getSnapCounts(pid, curr_week):
  cursor = makeCursor()
  cursor.execute("SELECT * FROM Snaps WHERE pid=%s" % (pid,))
  snap_counts = cursor.fetchone()
  
  if snap_counts == None:
    return [], 0, 0
  
  last_week = snap_counts[curr_week - 1]
  
  if last_week == 0:
    trend = snap_counts[curr_week - 2] - snap_counts[curr_week - 3]
  else:
    trend = last_week - snap_counts[curr_week - 2]
  comma = ","
  return comma.join(str(e) for e in snap_counts[1:curr_week]), last_week, trend

def getAccuracy(pid, curr_week):
  cursor = makeCursor()
  cursor.execute("SELECT * FROM Projections WHERE pid=%s" % (pid,))
  projections = cursor.fetchall()[0]
  cursor.execute("SELECT * FROM Actual WHERE pid=%s" % (pid,))
  actuals = cursor.fetchall()[0]
  #print(projections, actuals)
  total_accuracy = 0
  total_espn_accuracy = 0
  total_games = 0
  total_over = 0
  total_fp = 0
  div_by_zero = False
  for week in range(1,curr_week):
    proj = float(projections[week])
    espn_proj = float(projections[week+16])
    act = actuals[week]

    if proj != 0 and espn_proj != 0 and act != "0" and act != '-':
      #if pid == "28514":
      #  print(proj,act,total_over,total_games)
      act = float(act)
      
      accuracy = (1 - abs((act - proj) / act))
      if accuracy > 0:
        try:
          espn_accuracy = (1 - abs((act - espn_proj) / act))
          if espn_accuracy > 0:
            total_espn_accuracy += espn_accuracy
        except:
          div_by_zero = True
        total_accuracy += accuracy
        
        total_fp += act
        if act > proj:
          total_over += 1
        total_games += 1

  if total_games == 0:
    return 0,0,0,0,0,[],[]
  
  if div_by_zero:
    total_espn_accuracy = 0
  else:
    total_espn_accuracy = int((total_espn_accuracy / total_games) * 100)
  comma = ","
  return int((total_accuracy / total_games) * 100), total_espn_accuracy, total_over, (total_games - total_over), ("%.2f" % round((total_fp / total_games), 2)), comma.join(projections[1:curr_week]), comma.join(actuals[1:curr_week])

def createPlayer(pid, name, team):
  db_name = getName(pid)
  if db_name == None and pid != None:
    db = makeDB()
    db.cursor().execute("INSERT INTO Player (id, name, team) VALUES (%s,'%s', '%s')" % (pid, name, team.upper()))
    db.cursor().execute("INSERT INTO Actual (pid, w1, w2,w3,w4,w5,w6,w7,w8,w9,w10,w11,w12,w13,w14,w15,w16) VALUES (%s,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0)" % pid)
    db.cursor().execute("INSERT INTO Projections (pid, y1, y2,y3,y4,y5,y6,y7,y8,y9,y10,y11,y12,y13,y14,y15,y16,e1, e2,e3,e4,e5,e6,e7,e8,e9,e10,e11,e12,e13,e14,e15,e16) VALUES (%s,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0)" % pid)
    db.cursor().execute("INSERT INTO Snaps (pid,s1,s2,s3,s4,s5,s6,s7,s8,s9,s10,s11,s12,s13,s14,s15,s16) VALUES (%s,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0)" % pid)
    db.commit()

def createSnaps(db, pid, s):
  db.cursor().execute("INSERT INTO Snaps (pid,s1,s2,s3,s4,s5,s6,s7,s8,s9,s10,s11,s12,s13,s14,s15,s16) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)" % (pid,s[0],s[1],s[2],s[3],s[4],s[5],s[6],s[7],s[8],s[9],s[10],s[11],s[12],s[13],s[14],s[15]))
  db.commit()

def updateSnaps(pid, snap_counts):
  db = makeDB()
  cursor = db.cursor()
  cursor.execute("SELECT * FROM Snaps WHERE pid=%s" % pid)
  if cursor.fetchone() == None:
    createSnaps(db,pid,snap_counts)
    return

  for week in range(1,17):
    col = 's'+str(week)
    count = snap_counts[week-1]
    db.cursor().execute("UPDATE Snaps SET %s=%s WHERE pid=%s" % (col,count,pid))
  db.commit()

def updateStats(pid, week, proj, act):
  
  #print(week,pid,getName(pid),proj,act)
  db = makeDB()
  col = 'y'+str(week)
  db.cursor().execute("UPDATE Projections SET %s=%s WHERE pid=%s" % (col, proj, pid))

  col = 'w'+str(week)
  db.cursor().execute("UPDATE Actual SET %s='%s' WHERE pid=%s" % (col, act, pid))
  db.commit()

def updateESPNStats(pid, week, proj):
  db = makeDB()

  col = 'e'+str(week)
  db.cursor().execute("UPDATE Projections SET %s=%s WHERE pid=%s" % (col, str(proj), pid))

  db.commit()



