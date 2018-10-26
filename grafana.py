#!/usr/bin/python
import requests
import json
import re
import logging
import getpass
import time
import sys
import socket
from optparse import OptionParser

logger = logging.getLogger()
ip = socket.gethostbyname(socket.gethostname())
log_file = '/var/log/grafana/Import_%s.log' % (time.strftime('%Y%m%d_%H%M%S'))
headers={"Content-Type": 'application/json',
		 "Accept": 'application/json'}

def set_logger(logger):
	logger.setLevel(logging.INFO)
	formatter = logging.Formatter('[%(asctime)s %(levelname)s]: %(message)s')
	fh = logging.FileHandler(log_file)
	fh.setFormatter(formatter)
	logger.addHandler(fh)

def get_options():
	usage = "usage: %prog [options]"
	parser = OptionParser(usage=usage)
	parser.add_option("-u", "--username", dest="user", help="Set your grafana username.")
	parser.add_option("-p", "--password", dest="psword", help="Set your grafana passwor")
	options, args = parser.parse_args()
	return options

def format_output(text):
	num = len(text) + 4
	print ('*' * num)
	print ('  ' + text)
	print ('*' * num)

def log_output(msg):
	logger.info("****%s****" % msg)
	format_output(msg)

def skip(msg):
	print('\33[32m***[SKIP]: %s \33[0m' % msg)

def info(msg):
	print('\33[33m***[INFO]: %s \33[0m' % msg)

def error(msg):
	print('\n\33[35m***[ERROR]: %s \33[0m' % msg)

def set_user():
	user, psword = 'admin', 'admin'
	option = get_options()
	log_output("Set Grafana Username")
	if option.user:
		user_url = 'http://' + user + ':' + psword +'@' + ip + ':3000/api/users'
		get_user = requests.get(user_url, headers=headers)
		data = get_user.text.encode()
		data = json.loads(data.strip("[]"))
		data["login"] = option.user
		data = json.dumps(data)
		data = data.decode()
		put_user = requests.put(user_url+'/1', data=data, headers=headers)
		if put_user.status_code == 200:
			logger.info("%s %s" % (put_user,put_user.text))
			info("Username Updated!")
			user = option.user
		else:
			logger.error("Username Updated Error %s %s" % (put_user,put_user.text))
			error("Username Updated Error %s %s" % (put_user,put_user.text))
			sys.exit(1)
	else:		
		logger.warn("Skip update username.It will use default username.")
		skip("Skip update username.Use default username.")

	log_output("Set Grafana Username")
	if option.psword:
		psw_url = 'http://' + user + ':' + psword + '@' + ip + ':3000/api/user/password'
		psw = {"oldPassword":psword,"newPassword":option.psword,"confirNew":option.psword}
		psw = json.dumps(psw)
		psw = psw.decode()
		put_psw = requests.put(psw_url, data=psw, headers=headers)
		if put_psw.status_code == 200:
			logger.info("%s %s" % (put_psw,put_psw.text))
			info("Password Updated!")
			psword = option.psword
		else:
			logger.error("Password Update Error %s %s" % (put_psw,put_psw.text))
			error("Password Update Error %s %s" % (put_psw,put_psw.text))
			sys.exit(1)
	else:
		logger.warn("Skip update password. It will use default password.")
		skip("Skip update password. Use default password.")

	return user,psword	


def dashboard_import(user, psword):
	db_get_url = 'http://' + user + ':' + psword + '@' + ip + ':3000/api/dashboards/uid/vSTc90giz'
	db_url = 'http://' + user + ':' + psword + '@' + ip + ':3000/api/dashboards/db'
	log_output("Check Dashboard")
	check = requests.get(db_get_url, headers=headers)
	logger.info("%s %s" % (check, check.text))
	if check.status_code == 200:
		logger.info("This dashboard has been existed.\nSkip import this dashboard.")
		skip("This dashboard has been existed.\nSkip import this dashboard.")
	elif check.status_code == 404:
		info("Dashbord dosen't exist.")
		log_output("Start importing dashboard...")
		data = open('esgyn_dashboard.json')
		response = requests.post(db_url, data=data, headers=headers)
		logger.info("%s %s" % (response,response.text))
		if response.status_code == 200:
			logger.info("Dashboard import successfully!")
			info("Dashboard import successfully!")
		else:
			error("Dashboard Import Error %s %s"(response,response.text))
			logger.error("Dashboard Import Error %s %s" % (response,response.text))
	elif check.status_code != 200 and check.status_code != 404:
		error("Check error %s %s" % (check, check.text))
		logger.error("%s %s" % (check, check.text))

def datasource_import(user, psword):
	ds_get_url = 'http://' + user + ':' + psword + '@' + ip + ':3000/api/datasources/name/esgyn'
	ds_url = 'http://' + user + ':' + psword + '@' + ip + ':3000/api/datasources'
	log_output("Check Datasource")
	check = requests.get(ds_get_url, headers=headers)
	logger.info("%s %s" % (check, check.text))
	if check.status_code == 200:
		logger.info("This datasource has been existed.\nSkip import this datasource.")
		skip("This datasource has been existed.\nSkip import this datasource.")
	elif check.status_code == 404:
		info("Datasource doesn't exist.")
		log_output("Start importing datasource...")
		data = open('esgyn_datasource.json')
		response = requests.post(ds_url, data=data, headers=headers)
		logger.info("%s %s" % (response,response.text))
		if response.status_code == 200:
			logger.info("Datasource import successfully!")
			info("Datasource import successfully!")
		else:
			error("Datasource Import Error!")
			logger.error("Datasource Import Error %s %s" % (response,response.text))
			sys.exit(1)	
	elif check.status_code != 200 and check.status_code != 404:
		error("Check Error %s %s" % (check, check.text))
		logger.error("Check Error %s %s" % (check, check.text))
		sys.exit(1)

def run():
	try:
		set_logger(logger)
		print("\33[32m[Log file location]: %s \33[0m" % log_file)
		user, psword = set_user()
		datasource_import(user, psword)
		dashboard_import(user, psword)
	except IOError:
		error("Unexpected error: Need sudo permission.")

if __name__ == "__main__":
	run()
