#!/usr/bin/python

import subprocess
import sys
import time
import re
import os

cmd = 'edb_pdsh -a "lsof +L1 2>/dev/null | grep /SCR"'

def main():
    try:
        STFS_status = None
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        ts = int(time.time())
        stdout, stderr = p.communicate()
        if "/SCR" in stdout:
            STFS_status = False
        elif "/SCR" not in stdout:
            STFS_status = True
				
        if STFS_status:
            print("esgyn.stfs.running %d 1" % ts)
        else:
            print("esgyn.stfs.running %d 0" % ts)
        sys.stdout.flush()
	
    except:
        print "Unexpected error:", sys.exc_info()[0]

if __name__ == "__main__":
    sys.stdin.close()
    sys.exit(main())
