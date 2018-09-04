# -*- coding: utf-8 -*-

"""
This module manage all of the login / logout user workflow
"""

import json
import hashlib
import base64
import time
import pyotp
import logging
from flask import render_template, Blueprint, redirect, request, session, Response, flash
import ldap
from models import Application, UserDroit
from parameters import default_website, ldap_server, ldap_dn
from utils.user import has_otp_enabled, is_connected, check_totp, clear_session, ldap_login, signed_tab, require_totp, change_password, validate_topt_secret, enable_user_2factor
from utils.app import get_app
from utils.exceptions import PasswordToOldException

csoMain = Blueprint('csoMain', __name__, template_folder='templates')


@csoMain.route("/", methods=["GET", "POST"])
def main():
    """
    User profil page (if connected)
    """
    if is_connected():
        return render_template("me.html", username=session["username"], has_otp_enabled=has_otp_enabled())
    else:
        return redirect('/login?apps=admin&next=/')


@csoMain.route("/password", methods=["GET", "POST"])
def password_renew():
    """
    Handle the password change
    GET : next & apps are requested 'redirection' after password change (used if password change is triggered after a login)
    """
    if is_connected():
        old_password = request.form.get('old_password', "")
        new_password = request.form.get('new_password', "")

        next_page = request.args.get('next', None)
        apps = request.args.get('apps', None)
        
        if old_password and new_password:
            status, message = change_password(old_password, new_password, None)
            if not status:
                # Changing password failure
                flash("Erreur lors du changement de mot de passe ({})".format(message))
                # Next page is specified ? Keep it for further redirection.
                if next_page:
                    return redirect("/password?next={}&apps={}".format(next_page, apps))
                else:
                    return redirect("/password")
            else:
                # Changing password success
                session.pop('force_renew_password', None)
                # If Next page is specified, redirect to the requested app and url
                if next_page:
                    return redirect("/login?next={}&apps={}".format(next_page, apps))
                else:
                    return redirect("/")

        return render_template("password.html")
    else:
        return redirect('/login?apps=admin&next=/')


@csoMain.route("/otp", methods=["GET", "POST"])
def enable_otp():
    if has_otp_enabled():
        return redirect("/")
    elif is_connected():
        secret = request.form.get('secret', None)
        totp = request.form.get('totp', None)

        if (secret is not None) and (totp is not None) and validate_topt_secret(secret, totp) and enable_user_2factor(secret):
            return redirect("/")
        elif (secret is not None) and (totp is not None):
            flash("Activation impossible, le code fourni est incorrect")
            return redirect("/otp")

        return render_template("secret.html", secret=pyotp.random_base32())

    else:
        return redirect("/")


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

        # Final test, user password is expired ?
        if "password_expired" in session:
            flash("Vous devez changer votre mot de passe pour continuer.")
            return redirect("/password?next={}&apps={}".format(next_page, apps))
        else:
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
            # Can't bind
            logging.info("Error for {} from {} ({})".format(username, request.remote_addr, e))
            return redirect('/error?next=' + next_page)

    # Save the provided OTP code for next redirection
    session["topt_value"] = request.form.get('totp', "").replace(" ", "")

    return redirect("/login?next={}&apps={}".format(next_page, apps))


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
