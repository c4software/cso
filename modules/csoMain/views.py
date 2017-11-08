"""
This module manage all of the login / logout user workflow
"""

import json
import hashlib
import base64
import time
from flask import render_template, Blueprint, redirect, request, session, Response
import ldap
from models import Application, UserDroit
from parameters import default_website, ldap_server, ldap_dn


csoMain = Blueprint('csoMain', __name__, template_folder='templates')

def get_app_key(appName):
    """
    Recuperation de la clef en bdd
    """
    app = Application.query.filter(Application.nom == appName).first()
    if app is not None:
        return app.key
    else:
        return None

def ldap_login(username, password, key):
    """
        Gestion du login LDAP
    """
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
    jsonValues = json.dumps(tab, separators=(',', ':'))

    return (jsonValues, signature)

@csoMain.route("/")
def main():
    """ Nothing on / """
    return ""

@csoMain.route("/login")
def login():
    """
    This function ask the user for his login / password 
    or redirect to the requested page if already login
    """

    next = request.args.get('next', "")
    apps = request.args.get('apps', "default")
    error_message = session.get('error', '')

    session.pop('error', None)

    # Si la personne est connecte alors ==> On redirige.
    if "username" in session:
        # Recuperation des valeurs de login
        json_value = session['values']
        values = json.loads(json_value)

        # recuperation de la clef
        key = get_app_key(apps)

        # Calcul de la signature et preparation de l'array pour le mettre dans le POST
        json_value, signature = signed_tab(values, key)

        # Calcul de la base64 de l'arrayJson
        b64_json_value = base64.b64encode(json_value)
        return render_template("redirection.html",
                               next=next,
                               apps=apps,
                               values=b64_json_value,
                               signature=signature)

    return render_template("login.html", next=next, apps=apps, error=error_message)

@csoMain.route("/doLogin",methods=['POST','GET'])
def process_login():
    """
    Process the login request. 
    """
    next = request.form.get('next', "")
    apps = request.form.get('apps', "default")

    username = request.form.get('username', '')
    password = request.form.get('password', '')

    # Recuperation de la clef de l'application en base de donnees
    key = get_app_key(apps)
    if key is None:
        # Si la clef est inconnu on Abort
        session['error'] = "Application inconnue"
        return redirect('/login?next='+next+"&apps="+apps)

    # Tentative d'authentification sur la LDAP
    try:
        b64_json_value, signature = ldap_login(username, password, key)
        return render_template("redirection.html",
                               next=next, apps=apps,
                               values=b64_json_value,
                               signature=signature)
                              
    except Exception as e:
        session['error'] = "Login / Mot de passe incorrect"

    return redirect('/login?next='+next+"&apps="+apps)

@csoMain.route("/error" ,methods=['POST','GET'])
def error():
    """
    Generic message for the user
    """
    message = request.args.get('message', "Vous ne disposez pas des droits suffisants.")
    next_page = request.args.get('next', default_website)
    return render_template("error.html", message=message, next=next_page)

@csoMain.route("/islogin" ,methods=['GET'])
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

@csoMain.route("/logout" ,methods=['POST','GET'])
def logout():
    """
    Display the logout request to the user
    """
    next_page = request.args.get('next', "")
    if "username" not in session:
        return redirect(next_page)
    else:
        return render_template("logout.html", next=next_page)

@csoMain.route("/logoutApps" ,methods=['POST','GET'])
def logout_apps():
    """
    Just redirect to the disconnet url of the initial request (SEssion is untouched)
    """
    next_page = request.form.get('next', "")
    return redirect(next_page)

@csoMain.route("/logoutAll" ,methods=['POST','GET'])
def logout_all():
    """
    Remove local session. And redirect to the initial request
    """
    next_page = request.form.get('next', "")
    session.pop('username', None)
    session.pop('values', None)
    session.pop('signature', None)
    return redirect(next_page)
