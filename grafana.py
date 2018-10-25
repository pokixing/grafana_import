#!/usr/bin/python
import requests
import json
import re
import logging
import getpass
import time

logger = logging.getLogger()
log_file = '/var/log/grafana/Import_%s.log' % (time.strftime('%Y%m%d_%H%M%S'))
headers={"Content-Type": 'application/json',
		 "Accept": 'application/json'}

def set_logger(logger):
	logger.setLevel(logging.INFO)
	formatter = logging.Formatter('[%(asctime)s %(levelname)s]: %(message)s')
	fh = logging.FileHandler(log_file)
	fh.setFormatter(formatter)
	logger.addHandler(fh)

def user_input():
	user_info = {}
	user_info['user_url'] = raw_input("Please enter your Grafana's URL: ")
	if not re.search(r':\d+',  user_info['user_url']):
		user_info['user_url'] += ':3000'
	if 'http' in user_info['user_url'] or 'https' in user_info['user_url']:
		user_info['user_url'] = re.search(r'(?:(?:[0,1]?\d?\d|2[0-4]\d|25[0-5])\.){3}(?:[0,1]?\d?\d|2[0-4]\d|25[0-5]):(\d+)', user_info['user_url'])
	user_info['user_name'] = raw_input("Please enter your Grafana username: ")
	user_info['user_psw'] = getpass.getpass("Please enter your Grafana password: ")
	return user_info

def format_output(text):
	num = len(text) + 4
	print ('*' * num)
	print ('  ' + text)
	print ('*' * num)

def log_output(msg):
	logger.info("****%s****" % msg)
	format_output(msg)

def warn(msg):
	    print('\n\33[35m***[WARN]: %s \33[0m' % msg)

def error(msg):
	print('\n\33[35m***[ERROR]: %s \33[0m' % msg)

def dashboard_import():
	user_info = user_input()
	db_get_url = 'http://' + user_info['user_name'] + ':' + user_info['user_psw'] + '@' + user_info['user_url'] + '/api/dashboards/uid/vSTc90giz'
	db_url = 'http://' + user_info['user_name'] + ':' + user_info['user_psw'] + '@' + user_info['user_url'] + '/api/dashboards/db'
	log_output("Test Dashboard")
	test = requests.get(db_get_url, headers=headers)
	logger.info("%s : %s" % (test,test.text))
	if test.status_code == 200:
		logger.warn("This dashboard has been existed.")
		warn("This dashboard has been existed.")
	elif test.status_code == 404:
		log_output("Start importing dashboard...")
		data = open('esgyn_dashboard.json')
		response = requests.post(db_url, data=data, headers=headers)
		logger.info("%s : %s" % (response,response.text))
		if response.status_code == 200:
			log_output("Dashboard import successfully!")
		else:
			error("Dashboard import failed!")
			logger.error("%s : %s" % (response,response.text))

def datasource_import():
	user_info = user_input()
	ds_get_url = 'http://' + user_info['user_name'] + ':' + user_info['user_psw'] + '@' + user_info['user_url'] + '/api/datasources/name/esgyn'
	ds_url = 'http://' + user_info['user_name'] + ':' + user_info['user_psw'] + '@' + user_info['user_url'] + '/api/datasources'
	log_output("Test Datasource")
	test = requests.get(ds_get_url, headers=headers)
	logger.info("%s : %s" % (test,test.text))
	if test.status_code == 200:
		logger.warn("This datasource has been existed.")
		warn("This datasource has been existed.")
	elif test.status_code == 404:
		log_output("Start importing datasource...")
		data = open('esgyn_datasource.json')
		response = requests.post(ds_url, data=data, headers=headers)
		logger.info("%s : %s" % (response,response.text))
		if response.status_code == 200:
			log_output("Datasource import successfully!")
		else:
			error("Datasource import failed!")
			logger.error("%s : %s" % (response,response.text))
			#############

def run():
	try:
		set_logger(logger)
		get_url, db_url = user_input()
		print("\33[32m[Log file location]: %s \33[0m" % log_file)
		datasource_import()
		dashboard_import()

	except IOError:
		error("Unexpected error: Need sudo permission.")

if __name__ == "__main__":
	run()
