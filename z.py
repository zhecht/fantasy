

from tika import parser
import os
import re


raw = parser.from_file("report.pdf")
with open(f"out.csv", "w") as fh:
	fh.write(raw["content"])

with open("out.csv") as fh:
	lines = [line.strip() for line in fh.readlines() if line.strip()]

full_output = ""
output = ""
which = ""
file_idx = 0
for idx, line in enumerate(lines):
	if line.startswith("TEAM"):
		if idx != 0:
			which = " ".join(lines[idx - 1].split(" ")[:-1]).replace("-", "").replace(",", "").replace(" ", "_")
			output = line.replace(" ", ",").replace(",%", "%").replace("Tm,PPR", "Tm PPR")+"\n"
		else:
			output = line+"\n"
	elif line.startswith("RESULTS"):

		if which:
			with open(f"report/{which}.csv", "w") as fh:
				fh.write(output)
		else:
			with open(f"report/out0.csv", "w") as fh:
				fh.write(output)
		file_idx += 1
	else:
		m = re.search(r"(.*?) (?:RB|TE|WR) (.*?) \d", line)
		if m:
			player = m.group(2)
			output += line.split(player)[0].replace(" ", ",")+player+line.split(player)[1].replace(" ", ",")+"\n"

		#output += line+"\n"
