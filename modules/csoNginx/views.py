import base64, json, hashlib
from flask import Blueprint, redirect, request, session, abort
from models import Application

csoNginx = Blueprint('csoNginx', __name__)

@csoNginx.route('/checkAuth', methods=['POST'])
def checkAuth():
    signature = request.forms.get("signature")
    values = request.forms.get("values")
    if check_and_set_login(values, signature):
        return set_data(values)
    else:
        return expire_data()

@csoNginx.route("/auth")
def auth():
    if session.get("auth_username", None):
        return ""
    else:
        return abort(401)

def check_and_set_login(json_values, remote_hash):
    try:
        values = json.loads(base64.b64decode(json_values))
        values["key"] = "" #cso_app_key
        my_hash = hashlib.sha512(json.dumps(values, separators=(',', ':'))).hexdigest()
        values['key'] = ""
        if remote_hash == my_hash:
            return True
        else:
            return False
    except Exception as e:
        return False

def set_data(values):
    session['auth_username'] = values["username"]
    session['auth_group'] = values["group"]
    session['auth_level'] = values["level"]
    return redirect("/")

def expire_data():
    session.pop('auth_username')
    session.pop('auth_group')
    session.pop('auth_level')
    return abort(401)
