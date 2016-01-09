#!/usr/bin/env python

from functools import wraps
from flask import request, Response

def check_auth(username,password):
	"""The function checks username/password combo"""
	return username == "graham" and password == "learning"

def authenticate():
	"""Sends 401 response to enable basic auth"""
	return Response(
	'Could not verify your access level.\n'
	'You have to log in with proper credentials',
	401,
	{'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
	@wraps(f)
	def decorated(*args, **kwargs):
		auth = request.authorization
		if not auth or not check_auth(auth.username, auth.password):
			return authenticate()
		return f(*args, **kwargs)
	return decorated
