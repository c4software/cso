"""
This module manage all of the login / logout user workflow
"""

import json
import hashlib
import base64
import time
import pyotp
from flask import render_template, Blueprint, redirect, request, session, Response
import ldap
from models import Application, UserDroit
from parameters import default_website, ldap_server, ldap_dn

csoMain = Blueprint('csoMain', __name__, template_folder='templates')

def get_app_key(app_name):
    """
    Recuperation de la clef en bdd
    """
    app = Application.query.filter(Application.nom == app_name).first()
    if app is not None:
        return app.key
    else:
        return None

def ldap_login(username, password, apps):
    """
        Gestion du login LDAP
    """
    key = get_app_key(apps)
    ldap_connector = ldap.initialize(ldap_server)
    ldap_connector.simple_bind_s(ldap_dn.format(username), password)
    ldap_connector.unbind_s()

    # Recuperation des infos utilisateurs en BDD
    user = UserDroit.query.filter(UserDroit.username == username).first()
    if user is None:
        return_value = {"username": username, "group": "users", "level": 0, "key": '', "timeToken": ""}
    else:
        return_value = {"username": username, "group": user.group, "level": user.level, "key": '', "timeToken": ""}

    # Calcul du hash de la clef
    json_value, signature = signed_tab(return_value, key)
    b64_json_value = base64.b64encode(json_value)

    # On stock en Cookie + Session le fait que l'utilisateur soit connecte,
    # pour les futures demande de login
    session['username'] = username
    session['values'] = json_value

    return (b64_json_value, signature)

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

    return (json_value, signature)

def require_topt():
    """
    Current have enable TOTP ? 
    """
    if "saved_computer" in session and session["saved_computer"] == "1":
        return False
    else:
        user = UserDroit.query.filter(UserDroit.username == session["username"]).first()
        return user and user.secret

def check_totp(code):
    """
    Validate / check OTP.
    - If the TOTP is present in database (secret) check if provided code is valide.
    - If user exist and no OTP continue.
    """
    if "username" in session:
        # Find the user in database.
        user = UserDroit.query.filter(UserDroit.username == session["username"]).first()
        if user and user.secret:
            # If User exist and has a secret
            totp = pyotp.TOTP(user.secret)
            return totp.verify(code)
        elif not user:
            # User not exist
            return False
        else:
            # User exist and don't have any secret
            return True
    else:
        return False


@csoMain.route("/")
def main():
    """ Nothing on / """
    return ""

@csoMain.route("/login", methods=["GET", "POST"])
def login():
    """
    This function ask the user for his login / password
    or redirect to the requested page if already login
    """

    next_page = request.args.get('next', "")
    apps = request.args.get('apps', "default")
    totp_value = request.form.get('totp', "").replace(" ", "")
    save_computer = request.form.get("save_computer", "0");
    error_message = session.pop('error', "")

    # Si la personne est connecte alors ==> On redirige.
    if "username" in session:
        # Get the login values in session
        json_value = session['values']
        values = json.loads(json_value)

        # Get the key in databases
        key = get_app_key(apps)
        if key is None:
            # Application key unknown. Abort the request
            return redirect('/error')

        # Calculate the signature and prepare the data to create the POST values
        json_value, signature = signed_tab(values, key)

        # Test if user need to prodive a OTP Code
        if require_topt():
            if not check_totp(totp_value):
                # While code isn't valid... loop until user provide a good code
                return render_template("totp.html", next=next_page, apps=apps)
            else:
                # If the code is valide, check if user choose to save the current computer.
                if save_computer == "1":
                    session["saved_computer"] = "1"

        # Calculate the base64 representation to transmit safely
        return render_template("redirection.html",
                               next=next_page,
                               apps=apps,
                               values=base64.b64encode(json_value),
                               signature=signature)
    else:
        # User not logged, display the login page.
        return render_template("login.html",
                               next=next_page,
                               apps=apps,
                               error=error_message)

@csoMain.route("/doLogin", methods=['POST','GET'])
def process_login():
    """
    Process the login request.
    """
    next_page = request.form.get('next', "")
    apps = request.form.get('apps', "default")

    username = request.form.get('username', '')
    password = request.form.get('password', '')

    # If username and password is present
    if username and password:
        # Bind the user
        try:
            ldap_login(username, password, apps)
        except Exception as e:
            return redirect('/error')

    return redirect('/login?next='+next_page+"&apps="+apps)

@csoMain.route("/error", methods=['POST', 'GET'])
def error():
    """
    Generic message for the user
    """
    message = request.args.get('message', "Vous ne disposez pas des droits suffisants.")
    next_page = request.args.get('next', default_website)
    return render_template("error.html", message=message, next=next_page)

@csoMain.route("/islogin", methods=['GET'])
def is_login():
    """
    Test if user is currently logged-in (and use jsonp to use avoid CORS)
    """
    callback = request.args.get('callback', "callback")
    if "username" in session:
        resp = callback+"({\"data\":true})"
    else:
        resp = callback+"({\"data\":false})"

    return Response(response=resp, status=200, mimetype="application/javascript")

@csoMain.route("/logout", methods=['POST', 'GET'])
def logout():
    """
    Display the logout request to the user
    """
    next_page = request.args.get('next', "")
    if "username" not in session:
        return redirect(next_page)
    else:
        return render_template("logout.html", next=next_page)

@csoMain.route("/logoutApps", methods=['POST', 'GET'])
def logout_apps():
    """
    Just redirect to the disconnet url of the initial request (SEssion is untouched)
    """
    next_page = request.form.get('next', "")
    return redirect(next_page)

@csoMain.route("/logoutAll", methods=['POST', 'GET'])
def logout_all():
    """
    Remove local session. And redirect to the initial request
    """
    next_page = request.form.get('next', "")
    session.pop('username', None)
    session.pop('values', None)
    session.pop('signature', None)
    session.pop('saved_computer', None)
    return redirect(next_page)
