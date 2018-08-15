from flask import session
from models import UserDroit

def is_connected():
    return "username" in session

def has_otp_enabled():
    user = UserDroit.query.filter(UserDroit.username == session["username"]).first()
    return user and user.secret