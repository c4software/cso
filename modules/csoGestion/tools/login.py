"""
Functions used to validate the login to access to the administration.
"""

from functools import wraps
import base64
import json
import hashlib
import datetime
from flask import session, redirect

login_url = "/login?apps=admin&next=/admin/login"
login_key = "T680SvwrxNtWPxB4DAT2"

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_logged():
            return redirect(login_url)

        return f(*args, **kwargs)
    return decorated_function

def is_old_request(time_token):
    """
    Test if provided values for login are older than 10 minutes.
    """
    time_token = datetime.datetime.fromtimestamp(int(time_token))
    return time_token < datetime.datetime.now()-datetime.timedelta(minutes=10)

def do_login(jsonValues, securityKey):
    try:
        values = json.loads(base64.b64decode(jsonValues))
        values["key"] = login_key

        my_security_key = hashlib.sha512(json.dumps(values, separators=(',', ':'))).hexdigest()
        values['key'] = ""
        
        if not is_old_request(values["timeToken"]) and securityKey == my_security_key:
            session['user'] = values
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
