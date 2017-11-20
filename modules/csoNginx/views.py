"""
This module is used to manage the connection using the CSO with NGINX.
"""
import base64
import json
import hashlib
from flask import Blueprint, redirect, request, session, abort
from models import Application

csoNginx = Blueprint('csoNginx', __name__)

@csoNginx.route('/checkAuth', methods=['POST'])
def check_auth():
    """
    Process the login data provided in post by the CSO.
    Input POST (automatically provided by the CSO):
        - signature
        - values
    GET:
        - apps (the app name of your application, used to recover the secrect key)
    """
    apps = request.args.get('apps', "default")
    next_hop = request.args.get('next', "/")
    signature = request.form.get("signature", "")
    values = request.form.get("values", "")

    # Auth data is correct ?
    decoded_values = check_and_set_login(values, signature, apps)
    if decoded_values:
        return set_data(decoded_values, next_hop)
    else:
        return expire_data()

@csoNginx.route("/auth")
def auth():
    """
    This path will be used internaly by the nginx at each requests to test if user is "authenticated". (use the nginx auth_request)
    Return 200 if user is connected (according the session), or 401 if user need to authenticate.
    """
    if session.get("auth_username", None):
        return ""
    else:
        return abort(401)

def check_and_set_login(json_values, remote_hash, apps):
    """
    Validate the json_values and the remote hash according the apps name provided.
    """
    try:
        # Get the secret app key in the database.
        requested_application = Application.query.filter(Application.nom == apps).first()
        if not requested_application:
            return False

        # Decode the base64 and transform the json to python format
        values = json.loads(base64.b64decode(json_values))
        
        # Insert the "secret" key
        values["key"] = requested_application.key

        # Calculate the secret hash
        my_hash = hashlib.sha512(json.dumps(values, separators=(',', ':'))).hexdigest()

        # The secret key is no longer needed, remove it from values
        values['key'] = ""

        # Hash should match, if its not the case ? 
        # the data has been manipulated by someone during the authentication process
        if remote_hash == my_hash:
            return values
        else:
            return None
    except Exception as e:
        return False

def set_data(values, next_hop):
    """
    Save the currently connected user for the domain.
    """
    session['auth_username'] = values["username"]
    session['auth_group'] = values["group"]
    session['auth_level'] = values["level"]
    return redirect(next_hop)

def expire_data():
    """
    Remove saved currently connected user.
    """
    session.pop('auth_username')
    session.pop('auth_group')
    session.pop('auth_level')
    return abort(401)
