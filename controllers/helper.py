

def getAccuracy(curr_week, yahoo_proj, espn_proj, actual):
	total_games = 0
	total_accuracy = 0
	total_espn_accuracy = 0
	total_over = 0
	total_fp = 0
	div_by_zero = False
	if yahoo_proj != 0 and espn_proj != 0 and actual != "-" and float(actual) != 0:
		actual = float(actual)
		accuracy = (1 - abs((actual - yahoo_proj) / actual))
		if accuracy > 0:
			try:
				espn_accuracy = (1 - abs((actual - espn_proj) / actual))
				if espn_accuracy > 0:
					total_espn_accuracy += espn_accuracy
			except:
				div_by_zero = True
			total_accuracy += accuracy
			total_fp += actual

			if actual > yahoo_proj:
				total_over += 1
			total_games += 1

	if total_games == 0:
		return 0,0,0,0,0

	if div_by_zero:
		total_espn_accuracy = 0
	else:
		total_espn_accuracy = int((total_espn_accuracy / total_games) * 100)
	yahoo_accuracy = int((total_accuracy / total_games) * 100)
	return yahoo_accuracy, total_espn_accuracy, total_over, (total_games - total_over), ("%.2f" % round((total_fp / total_games), 2))

def getSnapCounts(curr_week):
	all_snap_counts = {}
	f = open("static/snap_counts.txt")
	for line in f:
		player, weekly_snap_counts = line.split("\t")
		weekly_snap_counts = [int(x) for x in weekly_snap_counts.split(",")]
		last_week = weekly_snap_counts[curr_week - 1]
		snap_counts = weekly_snap_counts[1:curr_week]

		if last_week == 0:
			trend = weekly_snap_counts[curr_week - 2] - weekly_snap_counts[curr_week - 3]
		else:
			trend = last_week - weekly_snap_counts[curr_week - 2]

		comma = ","
		all_snap_counts[player] = {"trend": trend, "counts": comma.join(str(e) for e in snap_counts[1:curr_week]), "last_week": last_week}
	return all_snap_counts