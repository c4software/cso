import base64, json, hashlib, sys
from flask import Blueprint, redirect, request, session, abort
from models import Application

csoNginx = Blueprint('csoNginx', __name__)

@csoNginx.route('/checkAuth', methods=['POST'])
def checkAuth():
    signature = request.forms.get("signature")
    values = request.forms.get("values")
    if check_and_set_login(values, signature):
        return redirect('/')
    else:
        return abort(401)

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
            set_data(values)
            return True
        else:
            expire_data()
            return False
    except Exception as e:
        expire_data()
        return False

def set_data(values):
    session['auth_username'] = values["username"]
    session['auth_group'] = values["group"]
    session['auth_level'] = values["level"]

def expire_data():
    session['auth_username'] = ""
    session['auth_group'] = ""
    session['auth_level'] = ""
