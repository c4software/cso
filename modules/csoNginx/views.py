import base64, json, hashlib, sys
from flask import Blueprint, redirect, request, session, Response, make_response, abort
from models import Application

csoNginx = Blueprint('csoNginx', __name__)

@csoNginx.route('/checkAuth', methods=['POST'])
def checkAuth():
    signature = request.forms.get("signature")
    values = request.forms.get("values")
    if do_login(values, signature):
        return redirect('/')
    else:
        return abort(401)

@csoNginx.route("/auth")
def auth():
    if session.get("auth_username", None):
        return ""
    else:
        return abort(401)


def do_login(values, signature):
    pass

def set_data(values):
    session['auth_username'] = values["username"]
    session['auth_group'] = values["group"]
    session['auth_level'] = values["level"]

def expire_data():
    session['auth_username'] = ""
    session['auth_group'] = ""
    session['auth_level'] = ""
