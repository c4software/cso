from flask import render_template, Blueprint, redirect, request, url_for
from modules.csoGestion.tools.login import login_required, do_login, do_logout
from modules.csoGestion.tools.generic import get_tbl_object, get_listing_redirection

from models import UserDroit, Application
from database import db_session

csoGestion = Blueprint('csoGestion', __name__, template_folder='templates')

@csoGestion.route("/")
@login_required
def index():
    """
    Display the main page
    """
    return render_template("index.html")

@csoGestion.route("/login", methods=['GET','POST'])
def login():
    """
    Do the login process
    """
    if do_login(request.form.get('values', request.args.get('values', '')), request.form.get('signature', request.args.get('signature', ''))):
        return redirect(url_for('csoGestion.index'))
    else:
        # Non autorise.
        return render_template('notAuthorized.html')

@csoGestion.route("/logout")
@login_required
def logout():
    """
    Logout the user
    """
    do_logout()
    return render_template('disconnect.html')

@csoGestion.route("/secret/list")
@login_required
def list_secret():
    """
    List user with secret
    """
    return None

@csoGestion.route("/<tbl_name>/list")
@login_required
def list_data(tbl_name):
    """
    List data in table name
    """
    try:
        tbl_object = get_tbl_object(tbl_name)
        objects = tbl_object.query.all()
        return render_template('list.html', list=objects, headers=tbl_object.header, action=tbl_name, key=tbl_object.primary_key)
    except Exception as e:
        return redirect(url_for('csoGestion.index'))

@csoGestion.route("/<tbl_name>/add")
@login_required
def add(tbl_name):
    """
    Add a new entry in the tbl_name
    """
    try:
        tbl_object = get_tbl_object(tbl_name)
        return render_template('formulaire.html', headers=tbl_object.header, action=tbl_name, key=tbl_object.primary_key, actionType="Ajouter")
    except Exception as e:
        return redirect(url_for('csoGestion.index'))

@csoGestion.route("/<tbl_name>/get/<get_element>")
@login_required
def get(tbl_name, get_element):
    """
    Get a specific element in the tbl_name
    """
    try:
        tbl_object = get_tbl_object(tbl_name)
        current = tbl_object.query.filter(tbl_object.primary_key+" == '"+get_element+"'").first()
        return render_template('formulaire.html', headers=tbl_object.header, action=tbl_name, key=tbl_object.primary_key, actionType="Modifier", object=current)
    except Exception as e:
        return redirect(url_for('csoGestion.index'))


@csoGestion.route("/<tbl_name>/save", methods=['POST','GET'])
@login_required
def save(tbl_name):
    """
    Save or update the Post data in the tbl_name
    """
    post_value = request.form
    tbl_Object = get_tbl_object(tbl_name)()

    # Remplissage de l'objet
    for curHeader in tbl_Object.header:
        if post_value[curHeader] == "":
            val = None
        else:
            val = post_value[curHeader]
        setattr(tbl_Object, curHeader, val)

    db_session.merge(tbl_Object)
    db_session.commit()
    return redirect(get_listing_redirection(tbl_name))

@csoGestion.route("/<tbl_name>/remove/<key>/confirm")
@login_required
def removeConfirm(key,tbl_name):
    """
    Ask if user confirm the deletion
    """
    return render_template('confirmation.html', tblName=tbl_name, key=key)

@csoGestion.route("/<tbl_name>/remove/<key>")
@login_required
def remove(key,tbl_name):
    """
    Delete the <key> element in the <tbl_name>
    """
    tbl_object = get_tbl_object(tbl_name)
    current = tbl_object.query.filter(tbl_object.primary_key+" == '"+key+"'").first()
    db_session.delete(current)
    db_session.commit()
    return redirect(get_listing_redirection(tbl_name))
