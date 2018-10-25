#!/usr/bin/python

import subprocess
import sys
import time
import re
import os

COLLECTION_INTERVAL = 1800
HDFS_DIR = '/user/trafodion'
cmd = "hdfs dfs -du -h " + HDFS_DIR

def main():
    try:
        while True:
            hdfs_used = 0
            p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            stdout, stderr = p.communicate()
            ts = int(time.time())
            stdout = stdout.split("\n")
            for i in stdout:
                i = i.split(" ")
                if i[0] != '':
                    hdfs_used += int(i[0]) 
            print("esgyn.data.size %d %s" % (ts, hdfs_used))
            sys.stdout.flush()
            time.sleep(COLLECTION_INTERVAL)
    
    except:
        print "Unexpected error:", sys.exc_info()[0]

if __name__ == "__main__":
    sys.stdin.close()
    sys.exit(main())
