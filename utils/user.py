import pyotp
import json
import hashlib
import base64
import time
import pyotp
import logging
import ldap
from flask import session
from parameters import default_website, ldap_server, ldap_dn
from models import UserDroit, Application
from utils.app import get_app

def is_connected():
    return "username" in session

def has_otp_enabled():
    user = UserDroit.query.filter(UserDroit.username == session["username"]).first()
    return user and user.secret

def change_password(new_password):
    pass

def check_totp(code, current_app):
    """
    Validate / check OTP.
    - If the TOTP is present in database (secret) check if provided code is valide.
    - If user exist and no OTP continue.
    """
    if is_connected():
        if is_opt_valid(code):
            return True
        elif current_app.otp_required == 1:
            # For this app the user should provide a valid code to access
            return False
        else:
            # User exist and don't have any secret falback
            return True
    else:
        return False

def is_opt_valid(code):
    user = UserDroit.query.filter(UserDroit.username == session["username"]).first()
    if user and user.secret:
        # If User exist and has a secret
        totp = pyotp.TOTP(user.secret)
        return totp.verify(code)
    else:
        # User not exist
        return False


def ldap_login(username, password, apps):
    """
        Gestion du login LDAP
    """
    current_app = get_app(apps)
    if current_app:
        key = current_app.key
    else:
        key = None

    ldap_connector = ldap.initialize(ldap_server)
    ldap_connector.simple_bind_s(ldap_dn.format(username), password)
    ldap_connector.unbind_s()

    # Recuperation des infos utilisateurs en BDD
    user = UserDroit.query.filter(UserDroit.username == username).first()
    if user is None:
        return_value = {"username": username, "group": "users", "level": 0, "twofactor": get_two_factor_level_signin(), "key": '', "timeToken": ""}
    else:
        return_value = {"username": username, "group": user.group + ",users", "level": user.level, "twofactor": get_two_factor_level_signin(), "key": '', "timeToken": ""}

    # Calcul du hash de la clef
    json_value, signature = signed_tab(return_value, key)
    b64_json_value = base64.b64encode(json_value)

    # On stock en Cookie + Session le fait que l'utilisateur soit connecte,
    # pour les futures demande de login
    session['username'] = username
    session['values'] = json_value

    return (b64_json_value, signature)


def get_two_factor_level_signin():
    """
        -	0 => Password Only
        -	1 => OTP
        -	2 => U2F
        -	3 => SMS
    """
    if "twofactor" in session:
        return session['twofactor']
    else:
        return "0"


def clear_session():
    """
    Clear all user data in session
    """
    session.pop('username', None)
    session.pop('values', None)
    session.pop('signature', None)
    session.pop('twofactor', None)
    session.pop('saved_computer', None)
    session.pop('topt_value', None)


def signed_tab(tab, key):
    """Calcul de la signature de l'array"""
    tab['timeToken'] = int(time.time())
    tab['key'] = key
    # Calcul de la signature de l element pour la securite
    signature = hashlib.sha512(json.dumps(tab, separators=(',', ':'))).hexdigest()

    # On supprime la clef car elle est secrete entre le CSO et l'application.
    # Elle est utile pour verifier que l'array n'a pas ete modifie
    tab["key"] = ""

    # Conversion de l'array en JSON
    json_value = json.dumps(tab, separators=(',', ':'))

    return json_value, signature


def require_totp(current_app):
    """
    Current user have enable TOTP ?
    """
    # Si l'utilisateur a sauvegarde l'ordinateur comme etant sur alors, on ne re-demande pas l'OTP
    if "saved_computer" in session and session["saved_computer"] == "1":
        return False
    else:
        # If current app required OTP return true
        if current_app.otp_required:
            return True
        else:
            # User have enable otp on his account ?
            return has_otp_enabled()        