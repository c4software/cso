"""
This module manage all of the login / logout user workflow
"""

import json
import hashlib
import base64
import time
import pyotp
import logging
from flask import render_template, Blueprint, redirect, request, session, Response
import ldap
from models import Application, UserDroit
from parameters import default_website, ldap_server, ldap_dn
from utils.user import has_otp_enabled, is_connected

csoMain = Blueprint('csoMain', __name__, template_folder='templates')


def get_app(app_name):
    """
    Return the requested in param
    """
    app = Application.query.filter(Application.nom == app_name).first()
    if app is not None:
        return app
    else:
        return None


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
    Current have enable TOTP ?
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


def check_totp(code, current_app):
    """
    Validate / check OTP.
    - If the TOTP is present in database (secret) check if provided code is valide.
    - If user exist and no OTP continue.
    """
    if is_connected():
        # Find the user in database.
        user = UserDroit.query.filter(UserDroit.username == session["username"]).first()
        if user and user.secret:
            # If User exist and has a secret
            totp = pyotp.TOTP(user.secret)
            return totp.verify(code)
        elif not user:
            # User not exist
            return False
        elif current_app.otp_required == 1:
            # For this app the user should provide a valid code to access
            return False
        else:
            # User exist and don't have any secret falback
            return True
    else:
        return False


@csoMain.route("/")
def main():
    if is_connected():
        return render_template("me.html", username=session["username"], has_otp_enabled=has_otp_enabled())
    else:
        return redirect('/error')


@csoMain.route("/password")
def password():
    if is_connected():
        return render_template("password.html")
    else:
        return redirect('/error')

@csoMain.route("/login", methods=["GET", "POST"])
def login():
    """
    This function ask the user for his login / password
    or redirect to the requested page if already login
    """

    next_page = request.args.get('next', "")
    apps = request.args.get('apps', "default")
    totp_value = request.form.get('totp', "").replace(" ", "")
    save_computer = request.form.get("save_computer", "0")
    error_message = session.pop('error', "")

    # Since the OTP code can be set in the main login form, get the save value from session.
    if "topt_value" in session:
        totp_value = session.pop('topt_value', None)

    # Si la personne est connecte alors ==> On redirige.
    if is_connected():
        # Get the login values in session
        json_value = session['values']
        values = json.loads(json_value)

        # Get the key in databases
        current_app = get_app(apps)
        if current_app is None:
            # Application key unknown. Abort the request
            return redirect('/error?next=' + next_page)

        # Calculate the signature and prepare the data to create the POST values
        json_value, signature = signed_tab(values, current_app.key)

        # Test if user need to prodive a OTP Code
        if require_totp(current_app):
            session["twofactor"] = "0"
            if totp_value and not check_totp(totp_value, current_app):
                # Code isn't valid. Abort the connexion
                return redirect('/error?next=' + next_page)
            elif not totp_value:
                # OTP required and no OTP, ask for it
                return render_template("totp.html", next=next_page, apps=apps)
            else:
                session["twofactor"] = "1"
                # If the code is valide, check if user choose to save the current computer.
                if save_computer == "1":
                    session["saved_computer"] = "1"
        else:
            session["twofactor"] = "0"

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


@csoMain.route("/doLogin", methods=['POST', 'GET'])
def process_login():
    """
    Process the login request.
    """
    next_page = request.form.get('next', "")
    apps = request.form.get('apps', "default")

    username = request.form.get('username', '')
    password = request.form.get('password', '')

    logging.info("New Connexion {} from {}".format(username, request.remote_addr))

    # If username and password is present
    if username and password:
        # Bind the user
        try:
            ldap_login(username, password, apps)
            logging.info("Success for {} from {}".format(username, request.remote_addr))
        except Exception as e:
            logging.info("Error for {} from {} ({})".format(username, request.remote_addr, e))
            return redirect('/error?next=' + next_page)

    # Save the provided OTP code for next redirection
    session["topt_value"] = request.form.get('totp', "").replace(" ", "")

    return redirect('/login?next='+next_page+"&apps="+apps)


@csoMain.route("/error", methods=['POST', 'GET'])
def error():
    """
    Generic message for the user
    """
    message = request.args.get('message', "Vous ne disposez pas des droits suffisants.")
    next_page = request.args.get('next', default_website)
    clear_session()
    return render_template("error.html", message=message, next=next_page)


@csoMain.route("/islogin", methods=['GET'])
def is_login():
    """
    Test if user is currently logged-in (Use jsonp to use avoid CORS)
    """
    callback = request.args.get('callback', "callback")
    if is_connected:
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
    if is_connected:
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
    clear_session()
    return redirect(next_page)
