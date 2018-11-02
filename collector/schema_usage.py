#!/usr/bin/python

import subprocess
import sys
import time
import re
import os

schema_usage = 0
COLLECTION_INTERVAL = 30
cmd = 'sqlci -q "select sum(store_file_size)/1024/1024 as store_size from table(cluster stats())"'

def main():
    global schema_usage
    try:
        while True:
 	    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
 	    stdout, stderr = p.communicate()
 	    ts = int(time.time())
	    index = stdout.split().index("STORE_SIZE")
	    schema_usage = stdout.split()[index+2]
 	    print("esgyn.schema.size %d %s" % (ts, schema_usage))
 	    sys.stdout.flush()
 	    time.sleep(COLLECTION_INTERVAL)

    except:
        print "Unexpected error:", sys.exc_info()[0]

if __name__ == "__main__":
    sys.stdin.close()
    sys.exit(main())
