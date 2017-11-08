from flask import render_template, Blueprint, redirect, request, session, Response
import ldap
import json
import hashlib
import base64
import time
from models import Application, UserDroit
from parameters import default_website, ldap_server, ldap_dn


csoMain = Blueprint('csoMain', __name__, template_folder='templates')

"""
Recuperation de la clef en bdd
"""
def getAppKey(appName):
    app = Application.query.filter(Application.nom == appName).first()
    if app is not None:
        return app.key
    else:
        return None
"""
    Envoi d'un header d'authentification
"""
def http_authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response('Could not verify your access level for that URL.\n'
                    'You have to login with proper credentials', 401,
                    {'WWW-Authenticate': 'Basic realm="Login Required"'})


"""
    Gestion du login LDAP
"""
def ldap_login(username, password, key):
    l = ldap.initialize(ldap_server)
    l.simple_bind_s(ldap_dn.format(username), password)
    print l.search_s(ldap_dn.format(username), ldap.SCOPE_SUBTREE, '(objectClass=*)')
    l.unbind_s()

    # Recuperation des infos utilisateurs en BDD
    user = UserDroit.query.filter(UserDroit.username == username).first()
    if user is None:
        returnValue = {"username": username, "group": "users", "level": 0, "key": '', "timeToken": ""}
    else:
        returnValue = {"username": username, "group": user.group, "level": user.level, "key": '', "timeToken": ""}

    # Calcul du hash de la clef
    jsonValues, signature = signedTab(returnValue, key)
    b64jsonValues = base64.b64encode(jsonValues)

    # On stock en Cookie + Session le fait que l'utilisateur soit connecte, pour les futures demande de login
    session['username'] = username
    session['values'] = jsonValues

    return (b64jsonValues, signature)

"""
Calcul de la signature de l'array
"""
def signedTab(tab, key):
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
    return redirect(default_website)

@csoMain.route("/login")
def login():
    next = request.args.get('next', "")
    apps = request.args.get('apps', "default")
    errorMessage = session.get('error', '')

    session.pop('error', None)

    # Si la personne est connecte alors ==> On redirige.
    if "username" in session:
        # Recuperation des valeurs de login
        jsonValues = session['values']
        values = json.loads(jsonValues)

        # recuperation de la clef
        key = getAppKey(apps)

        # Calcul de la signature et preparation de l'array pour le mettre dans le POST
        jsonValues, signature = signedTab(values, key)

        # Calcul de la base64 de l'arrayJson
        b64jsonValues = base64.b64encode(jsonValues)
        return render_template("redirection.html", next=next, apps=apps, values=b64jsonValues, signature=signature)
    
    return render_template("login.html", next=next, apps=apps, error=errorMessage)

@csoMain.route('/login_http')
def http_login():
    next = request.args.get('next', "")
    apps = request.args.get('apps', "default")

    # Recuperation de la clef de signature
    key = getAppKey(apps)
    if key is None:
        return redirect(default_website)

    if "username" in session:
        # Recuperation des valeurs de login
        jsonValues = session['values']
        values = json.loads(jsonValues)

        # recuperation de la clef
        key = getAppKey(apps)

        # Calcul de la signature et preparation de l'array pour le mettre dans le POST
        jsonValues, signature = signedTab(values, key)

        # Calcul de la base64 de l'arrayJson
        b64jsonValues = base64.b64encode(jsonValues)

        return redirect(next+"?values="+b64jsonValues+"&signature="+signature)
    else:
        # L'utilisateur n'est pas connu en session, on le log avec les id qu'il va fournir
        auth = request.authorization
        if not auth:
            return http_authenticate()
        else:
            try:
                b64jsonValues, signature = ldap_login(auth.username, auth.password, key)
                return redirect(next+"?values="+b64jsonValues+"&signature="+signature)
                # Login OK.
            except:
                # Login NOK
                return http_authenticate()


@csoMain.route("/doLogin",methods=['POST','GET'])
def process_login():
    next = request.form.get('next', "")
    apps = request.form.get('apps', "default")

    username = request.form.get('username', '')
    password = request.form.get('password', '')

    # Recuperation de la clef de l'application en base de donnees
    key = getAppKey(apps)
    if key is None:
        # Si la clef est inconnu on Abort
        session['error'] = "Application inconnue"
        return redirect('/login?next='+next+"&apps="+apps)

    # Tentative d'authentification sur la LDAP
    returnValue = {}

    try:
        b64jsonValues, signature = ldap_login(username, password, key)
        return render_template("redirection.html", next=next, apps=apps, values=b64jsonValues, signature=signature)
    except:
        session['error'] = "Login / Mot de passe incorrect"

    return redirect('/login?next='+next+"&apps="+apps)

@csoMain.route("/error" ,methods=['POST','GET'])
def error():
    message = request.args.get('message', "Vous ne disposez pas des droits suffisants.")
    next = request.args.get('next', default_website)
    return render_template("error.html", message=message, next=next)

@csoMain.route("/islogin" ,methods=['GET'])
def islogin():
    callback = request.args.get('callback', "callback")
    if "username" in session:
        resp = callback+"({\"data\":true})"
    else:
        resp = callback+"({\"data\":false})"

    return Response(response=resp, status=200, mimetype="application/javascript")

@csoMain.route("/logout" ,methods=['POST','GET'])
def logout():
    next = request.args.get('next', "")
    if "username" not in session:
        return redirect(next)
    else:
        return render_template("logout.html", next=next)

@csoMain.route("/logoutApps" ,methods=['POST','GET'])
def logoutApps():
    next = request.form.get('next', "")
    return redirect(next)

@csoMain.route("/logoutAll" ,methods=['POST','GET'])
def logoutAll():
    next = request.form.get('next',"")
    session.pop('username', None)
    session.pop('values', None)
    session.pop('signature', None)
    return redirect(next)
