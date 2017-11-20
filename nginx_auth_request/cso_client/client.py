"""
Standalone script to handle the CSO connexion and check state for NGINX auth_request process 
"""

import base64
import json
import hashlib
import sys
import datetime
from bottle import route, run, template, request, response, HTTPResponse, redirect

if len(sys.argv) < 2:
    print("To use the cso_client you need to provide a CSO app key. \r\nExample : {0} mWgBV6mKZ3nwhwpvMBxx".format(sys.argv[0]))
    sys.exit()

cso_app_key = sys.argv[1]

@route('/checkAuth', method='POST')
def check_auth():
    """
    Process the login data provided in post by the CSO.
    Input POST (automatically provided by the CSO):
        - signature
        - values
    """
    signature = request.forms.get("signature")
    values = request.forms.get("values")
    if do_login(values, signature):
        return redirect('/')
    else:
        return HTTPResponse(status=401)

@route("/auth")
def auth():
    """
    This path will be used internaly by the nginx at each requests to test if user is "authenticated". (use the nginx auth_request)
    Return 200 if user is connected (according the session), or 401 if user need to authenticate.
    """
    if request.get_cookie("auth_username", secret=cso_app_key):
        return HTTPResponse(status=200)
    else:
        return HTTPResponse(status=401)

def is_old_request(time_token):
    """
    Test if provided values for login are older than 10 minutes.
    """
    time_token = datetime.datetime.fromtimestamp(int(time_token))
    return time_token < datetime.datetime.now()-datetime.timedelta(minutes=10)

def do_login(json_values, remote_hash):
    """
    Validate the json_values and the remote hash according the secret_key.
    """
    try:
        # Decode the base64 and transform the json to python format
        values = json.loads(base64.b64decode(json_values))

        # Insert the "secret" key
        values["key"] = cso_app_key

        # Calculate the secret hash
        my_hash = hashlib.sha512(json.dumps(values, separators=(',', ':'))).hexdigest()

        # The secret key is no longer needed, remove it from values
        values['key'] = ""

        # Hash should match, if its not the case ?
        # the data has been manipulated by someone during the authentication process
        if not is_old_request(values["timeToken"]) and remote_hash == my_hash:
            set_cookie(values)
            return True
        else:
            expire_cookie()
            return False
    except Exception as e:
        expire_cookie()
        return False

def set_cookie(values):
    """
    Save the current auth in cookie.
    """
    response.set_cookie('auth_username', values["username"], httponly=True, secret=cso_app_key)
    response.set_cookie('auth_group', values["group"], httponly=True, secret=cso_app_key)
    response.set_cookie('auth_level', values["level"], httponly=True, secret=cso_app_key)

def expire_cookie():
    """
    Expire the cookie on authentication failure.
    """
    response.set_cookie('auth_username', "", expires=0, secret=cso_app_key)
    response.set_cookie('auth_group', "", expires=0, secret=cso_app_key)
    response.set_cookie('auth_level', "", expires=0, secret=cso_app_key)


run(host='localhost', port=8000)