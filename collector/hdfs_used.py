#!/usr/bin/python

import subprocess
import sys
import time
import re
import os

HDFS_DIR = '/user/trafodion'
cmd = "hdfs dfs -du -h " + HDFS_DIR

def main():
    try:
        hdfs_used = 0
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        ts = int(time.time())
        for line in p.stdout.readlines():
            line = line.split()
            hdfs_used += eval(line[0])
        print("esgyn.data.size %d %s" % (ts, hdfs_used))
        sys.stdout.flush()

    except:
        print "Unexpected error:", sys.exc_info()[0]

if __name__ == "__main__":
    sys.stdin.close()
    sys.exit(main())
