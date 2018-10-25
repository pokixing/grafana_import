#!/usr/bin/python

import subprocess
import sys
import time
import re
import os

COLLECTION_INTERVAL = 30
cmd = "pstat"

def main():
	try:
		while True:
			esgyn_memory, monitor_memory, tm_memory, mxosrvr_memory = 0, 0, 0, 0
			p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
			ts = int(time.time())
			for line in p.stdout.readlines():
				line_split = line.split()
				if (len(line_split) != 0) and (line_split[0] == "trafodion"):
					esgyn_memory += eval(line_split[4])
					if re.search("monitor*", line):
 						monitor_memory += eval(line_split[4])
					elif re.search("tm", line):
						tm_memory += eval(line_split[4])
					elif re.search("mxosrvr", line):
						mxosrvr_memory += eval(line_split[4])
				
				else:
					continue
			
			print("esgyndb.memory.usage %d %s" % (ts, esgyn_memory/1024))
			print("esgyndb.tm.memory %d %s" % (ts, tm_memory/1024))
			print("esgyndb.monitor.memory %d %s" % (ts, monitor_memory/1024))
			print("esgyndb.mxosrvr.memory %d %s" % (ts, mxosrvr_memory/1024))
			sys.stdout.flush()
			time.sleep(COLLECTION_INTERVAL)
	except:
		print("Unexpected error:", sys.exc_info()[0])

if __name__ == "__main__":
	sys.stdin.close()
	sys.exit(main())
