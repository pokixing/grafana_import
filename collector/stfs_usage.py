#!/usr/bin/python

import subprocess
import sys
import time
import re
import os

COLLECTION_INTERVAL = 30
cmd = '''echo `dtmci showenv STFS_HDD_LOCATION` | gawk -v OFS="\n" 'BEGIN{FS=":"} {$1=$1;if(NF==1) print $1; else print $1,$NF}' '''

def main():
        try:
                while True:
			stfs = []
                        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                        ts = int(time.time())
			stdout,stderr = p.communicate()
			stdout = stdout.split()
			for line in stdout:
				df_cmd = "df -k " + line
				du_cmd = "du -k --max-depth=0 " + line
				
				p1 = subprocess.Popen(df_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
				df_stdout,df_stderr = p1.communicate()
				df_stdout = df_stdout.split('\n')[1].split()
				filesys, filefree = df_stdout[0], df_stdout[3]
				
				p2 = subprocess.Popen(du_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
				du_stdout,du_stderr = p2.communicate()
				stfsusage = du_stdout.split()[0]
				stfs.append([line,filesys,stfsusage,filefree])
			
			stfs_usage,file_free = 0,0
			file_sys = []
			for i in stfs:
				stfs_usage += eval(i[2])
				if i[1] in file_sys:
					file_sys.append(i[1])
				elif i[1] not in file_sys:
					file_sys.append(i[1])
					file_free += eval(i[3])
			
			stfs_prect = (float(stfs_usage)/file_free) * 100
			print("esgyn.stfs.prect %d %.5s" % (ts,stfs_prect))
                        time.sleep(COLLECTION_INTERVAL)

        except:
                print "Unexpected error:", sys.exc_info()[0]

if __name__ == "__main__":
    sys.stdin.close()
    sys.exit(main())

