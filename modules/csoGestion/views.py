from flask import render_template, Blueprint, redirect, request, url_for
from modules.csoGestion.tools.login import login_required, do_login, do_logout
from modules.csoGestion.tools.generic import get_tbl_object, get_listing_redirection

from models import UserDroit, Application
from database import db_session

csoGestion = Blueprint('csoGestion', __name__, template_folder='templates')

@csoGestion.route("/")
@login_required
def index():
    return render_template("index.html")

@csoGestion.route("/login", methods=['GET','POST'])
def login():
    if do_login(request.form.get('values', request.args.get('values', '')), request.form.get('signature', request.args.get('signature', ''))):
        return redirect(url_for('csoGestion.index'))
    else:
        # Non autorise.
        return render_template('notAuthorized.html')

@csoGestion.route("/logout")
@login_required
def logout():
    do_logout()
    return render_template('disconnect.html')

#
# List tblName
#
@csoGestion.route("/<tblName>/list")
@login_required
def list(tblName):
    try:
        tbl_object = get_tbl_object(tblName)
        objects = tbl_object.query.all()
        return render_template('list.html', list=objects, headers=tbl_object.header, action=tblName, key=tbl_object.primary_key)
    except Exception as e:
        return redirect(url_for('csoGestion.index'))

@csoGestion.route("/<tblName>/add")
@login_required
def add(tblName):
    try:
        tbl_object = get_tbl_object(tblName)
        return render_template('formulaire.html', headers=tbl_object.header, action=tblName, key=tbl_object.primary_key, actionType="Ajouter")
    except Exception as e:
        return redirect(url_for('csoGestion.index'))

@csoGestion.route("/<tblName>/get/<getElement>")
@login_required
def get(tblName, getElement):
    try:
        tbl_object = get_tbl_object(tblName)
        current = tbl_object.query.filter(tbl_object.primary_key+" == '"+getElement+"'").first()
        return render_template('formulaire.html', headers=tbl_object.header, action=tblName, key=tbl_object.primary_key, actionType="Modifier", object=current)
    except Exception as e:
        return redirect(url_for('csoGestion.index'))

#
# Sauvegarde ou Update
#
@csoGestion.route("/<tblName>/save", methods=['POST','GET'])
@login_required
def save(tblName):
    postValue = request.form
    tbl_Object = get_tbl_object(tblName)()

    # Remplissage de l'objet
    for curHeader in tbl_Object.header:
        if postValue[curHeader] == "":
            val = None
        else:
            val = postValue[curHeader]
        setattr(tbl_Object, curHeader, val)

    db_session.merge(tbl_Object)
    db_session.commit()
    return redirect(get_listing_redirection(tblName))


#
# Confirmation Remove tblName
#
@csoGestion.route("/<tblName>/remove/<key>/confirm")
@login_required
def removeConfirm(key,tblName):
    return render_template('confirmation.html', tblName=tblName, key=key)

#
# Remove tblName
#
@csoGestion.route("/<tblName>/remove/<key>")
@login_required
def remove(key,tblName):
    tbl_object = get_tbl_object(tblName)
    current = tbl_object.query.filter(tbl_object.primary_key+" == '"+key+"'").first()
    db_session.delete(current)
    db_session.commit()
    return redirect(get_listing_redirection(tblName))
