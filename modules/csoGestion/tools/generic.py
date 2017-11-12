"""
Generic Method to deal with the database
"""

from models import UserDroit, Application
from flask import url_for

def get_tbl_object(tbl_name):
    """
    Return the table object according the table name.
    """
    return {
        "users":UserDroit,
        "apps":Application,
    }[tbl_name]

def get_listing_redirection(tbl_name):
    """
    Return the url for "list_data" for each table
    """
    return {
        "users":url_for("csoGestion.list_data", tbl_name=tbl_name),
        "apps":url_for("csoGestion.list_data", tbl_name=tbl_name),
    }[tbl_name]
