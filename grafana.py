#!/usr/bin/python
import os
import requests
import json
import logging
import time
import sys
import socket
import subprocess
import ConfigParser
from optparse import OptionParser

logger = logging.getLogger()
TMP_USERINFO = "/tmp/grafana_userinfo"
GRA_CONFILE = "/etc/grafana/grafana.ini"
log_file = '/var/log/grafana/Import_%s.log' % (time.strftime('%Y%m%d_%H%M%S'))


def set_logger(logger):
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('[%(asctime)s %(levelname)s]: %(message)s')
    fh = logging.FileHandler(log_file)
    fh.setFormatter(formatter)
    logger.addHandler(fh)


def get_options():
    usage = "usage: %prog [options]"
    parser = OptionParser(usage=usage)
    parser.add_option("-p", "--password", dest="admin_psword",
                      help="Modify the grafana administrator password.")
    parser.add_option("-e", "--editor", dest="editor",
                      help="Create a user with editing authority. You need to enter username, password and email address \
                           (this mailbox will be used to receive alarm messages) in order and separated them by comma. \
                      i.e. \"esgyn,password,esgyn@esgyn.cn\"")
    parser.add_option("-s", "--smtp", dest="smtp",
                      help="Set the mailbox to send the alarm message. You need to enter email address, smtp server \
                      and password in order and separated them by comma. i.e. \"esgyn@qq.com,smtp.qq.com,password\"")
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


def error(msg, logout=True):
    print('\n\33[35m***[ERROR]: %s \33[0m' % msg)
    if logout: logger.error(msg)
    sys.exit(1)


def load_user():
    if os.path.exists(TMP_USERINFO):
        with open(TMP_USERINFO, "r") as user_info:
            userinfo = json.load(user_info)
    else:
        userinfo = {"user": "admin", "psword": "admin"}
    return userinfo["user"], userinfo["psword"]


class Grafana(object):
    def __init__(self, admin_user, admin_psword):
        self.admin_user = admin_user
        self.admin_psword = admin_psword
        self.ip = socket.gethostbyname(socket.gethostname())
        self.url = 'http://%s:%s@%s' % (self.admin_user, self.admin_psword, self.ip)
        self.headers = {"Content-Type": 'application/json',
                        "Accept": 'application/json'}

    def switch_request(self, mode, api, data=""):
        url = self.url + api
        data = json.dumps(data)
        switcher = {
            "get": requests.get(url, headers=self.headers),
            "put": requests.put(url, data=data, headers=self.headers),
            "post": requests.post(url, data=data, headers=self.headers),
            "patch": requests.patch(url, data=data, headers=self.headers)
        }
        return switcher.get(mode, "Nothing")

    def set_admin_psw(self, new_admin_psword):
        log_output("Set Admin Password")
        psw_api = ':3000/api/user/password'
        data = {"oldPassword": self.admin_psword, "newPassword": new_admin_psword, "confirNew": new_admin_psword}
        put_psw = self.switch_request("put", psw_api, data)
        if put_psw.status_code == 200:
            logger.info("Admin password Updated!  %s %s" % (put_psw, put_psw.text))
            info("Admin password Updated!")
            self.admin_psword = new_admin_psword
            self.url = 'http://%s:%s@%s' % (self.admin_user, self.admin_psword, self.ip)
        else:
            error("Password Update Error %s %s" % (put_psw, put_psw.text))

    def set_editor(self, editor, editor_psword, email):
        log_output("Create Editor")
        editor_api = ':3000/api/admin/users'
        data = {"name": editor, "email": email, "login": editor, "password": editor_psword}
        editor = self.switch_request("post", editor_api, data)
        if editor.status_code == 200:
            editor_id = json.loads(editor.text)["id"]
            org_api = ':3000/api/org/users/' + str(editor_id)
            data = {"role": "Editor"}
            self.switch_request("patch", org_api, data)
            logger.info("Editor created successfully!  %s %s" % (editor, editor.text))
            info("Editor created successfully!")
        elif editor.status_code == 500:
            logger.info("This editor has been created.\nSkip create this editor.")
            skip("This editor has been created.\nSkip create this editor.")
        else:
            error("Editor created Error %s %s" % (editor, editor.text))

    def notification_import(self, receive_addr):
        log_output("Start importing alert notification...")
        noti_api = ':3000/api/alert-notifications'
        data = {"sendReminder": False, "type": "email", "name": "Esgyndb Notification", "isDefault": False, "settings": {"addresses": ""}}
        data["settings"]["addresses"] = receive_addr
        response = self.switch_request("post", noti_api, data)
        if response.status_code == 200:
            logger.info("Alert notification import successfully!")
            info("Alert notification import successfully!")
        elif response.status_code == 500:
            logger.info("This notifiction has been existed.\nSkip import this notifiction.")
            skip("This notification has been existed.\nSkip import this notifiction.")
        else:
            error("Alert Notification Import Error %s %s" % (response, response.text))

    def templet_import(self, mode, ds_name):  # import dashbord or datasource
        title = ds_name + ' ' + mode
        if mode == 'dashboard':
            get_api = ':3000/api/dashboards/uid/esgyndb'
            imp_url = self.url + ':3000/api/dashboards/db'
        elif mode == 'datasource':
            get_api = ':3000/api/datasources/name/%s' % ds_name.lower()
            imp_url = self.url + ':3000/api/datasources'
        log_output("Check %s" % title)
        check = self.switch_request("get", get_api)
        logger.info("%s %s" % (check, check.text))
        if check.status_code == 200:
            logger.info("This %s has been existed.\nSkip import this %s." % (title, title))
            skip("This %s has been existed.\nSkip import this %s." % (title, title))
        elif check.status_code == 404:
            info("%s dosen't exist." % title)
            log_output("Start importing %s..." % title)
            data = open('%s_%s.json' % (ds_name.lower(), mode.lower()), 'rb')
            response = requests.post(imp_url, data=data, headers=self.headers)
            logger.info("%s %s" % (response, response.text))
            if response.status_code == 200:
                logger.info("%s import successfully!" % title)
                info("%s import successfully!" % title)
            else:
                error("%s Import Error %s %s" % (mode, response, response.text))
        elif check.status_code != 200 and check.status_code != 404:
            error("Check error %s %s" % (check, check.text))

    def start_db(self):
        log_output("Start Dashboard")
        search_api = ':3000/api/search'
        search = self.switch_request("get", search_api)
        data = search.text.encode()
        data = json.loads(data)
        for d in data:
            if d["uid"] == "esgyndb":
                db_id = d["id"]
                break
        start_api = ':3000/api/user/stars/dashboard/' + str(db_id)
        start = self.switch_request("post", start_api)
        if start.status_code == 200:
            logger.info("%s %s" % (start, start.text))
            info("Dashboard started")
        elif start.status_code == 500:
            logger.info("%s %s" % (start, start.text))
            skip("This dashboard has been started.\nSkip this process.")
        else:
            error("Dashboard Start Error %s %s" % (start, start.text))

    def set_smtp(self, sendmail, smtp_host, smtp_psword):
        data = """enabled=true                                                                                                                                              
host=%s
user=%s
password=%s
from_address=%s
from_name = Grafana
""" % (smtp_host, sendmail, smtp_psword, sendmail)
        log_output("Set grafana.ini")
        if os.path.exists(GRA_CONFILE):
            confile = open(GRA_CONFILE).readlines()
            lines = []
            config = ConfigParser.ConfigParser()
            config.read(GRA_CONFILE)
            item = config.items('smtp')
            for i in range(len(confile)):
                lines.append(confile[i])
                if "[smtp]" in confile[i]:
                    linenum = i
            if item:
                logger.info("Skip set grafana.ini. It has been changed.")
                skip("Skip set grafana.ini. It has been changed.")
            elif not item:
                lines.insert(linenum+1, data)
                s = ''.join(lines)
                with open(GRA_CONFILE, 'w') as confile:
                    confile.write(s)
                p = subprocess.Popen("sudo service grafana-server restart", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                info("Set Grafana.ini Complete")
        else:
            error("%s doesn't exist" % GRA_CONFILE)


def run():
    try:
        set_logger(logger)
        option = get_options()
        print("\33[32m[Log file location]: %s \33[0m" % log_file)
        admin_user, admin_psword = load_user()
        grafana = Grafana(admin_user, admin_psword)
        if option.admin_psword:
            grafana.set_admin_psw(option.admin_psword)
            admin_psword = option.admin_psword
        if option.editor:
            option.editor = option.editor.split(',')
            if len(option.editor) == 3:
                editor, editor_psword, editor_email = option.editor
                grafana.set_editor(editor.strip(), editor_psword.strip(), editor_email.strip())
            else:
                error("You need input email;host;psword(eg)")
        grafana.templet_import('datasource', 'Esgyn')
        grafana.templet_import('datasource', 'Loki')
        grafana.templet_import('dashboard', 'Esgyn')
        if option.smtp:
            if editor_email: grafana.notification_import(editor_email.strip())
            option.smtp = option.smtp.split(',')
            if len(option.smtp) == 3:
                sendmail, smtp_host, smtp_psword = option.smtp
                grafana.set_smtp(sendmail.strip(), smtp_host.strip(), smtp_psword.strip())
            else:
                error("You need input email;host;psword(eg)")
        grafana.start_db()
        if os.path.exists(TMP_USERINFO):
            os.remove(TMP_USERINFO)
        log_output("Import Complete")
    except SystemExit:
        user_info = {"user": admin_user, "psword": admin_psword}
        with open(TMP_USERINFO, "w") as userinfo:
            json.dump(user_info, userinfo)
        error("Please check the error according log file: %s" % log_file, logout=False)


if __name__ == "__main__":
    run()

