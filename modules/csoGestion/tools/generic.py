from models import UserDroit, Application
from flask import url_for

def get_tbl_object(tblName):
    return {
        "users":UserDroit,
        "apps":Application,
    }[tblName]

def get_listing_redirection(tblName):
    return {
        "groups":url_for("csoGestion.list", tblName=tblName),
        "users":url_for("csoGestion.list", tblName=tblName),
        "apps":url_for("csoGestion.list", tblName=tblName),
    }[tblName]
