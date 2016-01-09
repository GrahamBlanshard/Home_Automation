#!/usr/bin/env python

#
# Import user modules
#
import sys, os, inspect
usr_mods = os.path.realpath(os.path.abspath(os.path.join(os.path.split(inspect.getfile( inspect.currentframe() ))[0],"securitypi")))
if usr_mods not in sys.path:
	sys.path.insert(0, usr_mods)

#Thanks: http://stackoverflow.com/a/6098238

###########
# IMPORTS #
###########
from securitypi.web import *
from flask import Flask,redirect
import sqlite3

##########
# CONFIG #
##########

#Flask
app = Flask(__name__)

#SQL
conn=sqlite3.connect('db/garage.db')
curs=conn.cursor()

#############
# FUNCTIONS #
#############
def door_status():
	try:
		curs.execute('SELECT source,name,etime FROM events ORDER BY ID DESC LIMIT 5')
		data = curs.fetchone()
		if data == None:
			return 'No events to report'
		else:
			return data[0] + ' last state = `' + data[1] + '` at ' + data[2]
	except sqlite3.Error, e:
		return 'Error %s:' % e.args[0]

##################
# FLASK FUNCIONS #
##################
@app.route('/user-auth')
@requires_auth
def secret_page():
	return redirect('/status/1234',code=302)

@app.route('/status/<code>')
def status(code):
	if code == "1234":
		return door_status() 
	else:
		return '<a href="user-auth">Who are you again?</a>'

@app.route('/status')
def status_plain():
	return '<a href="user-auth">Please authenticate</a>'

########
# MAIN #
########
if __name__ == '__main__':
	app.run(host="0.0.0.0")
	if conn:
		conn.close()
