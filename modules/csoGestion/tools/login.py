from functools import wraps
from flask import session, request, redirect, url_for
import base64
import json
import hashlib

from parameters import login_url

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
		if not is_logged():
			return redirect(login_url)

		return f(*args, **kwargs)
    return decorated_function

def do_login(jsonValues, securityKey):
	try:
		values = json.loads(base64.b64decode(jsonValues))
		values["key"] = "T680SvwrxNtWPxB4DAT2"

		mySecurityKey = hashlib.sha512(json.dumps(values, separators=(',',':'))).hexdigest()
		values['key'] = ""

		if securityKey == mySecurityKey:
			session['user'] = values
			groups = values['group'].split(',')
			if 'admin' in values['group'].split(','):
				return True
			else:
				return False

		else:
			return False
	except:
		return False

def do_logout():
	session.pop('user', None)

def is_logged():
	if 'user' in session:
		return True
