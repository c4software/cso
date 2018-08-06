"""
Main file of CSO application
"""

import uuid
from flask import Flask, render_template, request, session, abort
from modules.csoMain.views import csoMain
from modules.csoGestion.views import csoGestion
from modules.csoNginx.views import csoNginx
import logging

app = Flask(__name__)
app.secret_key = "9jHy6lAOxBKzhbY3eeGRB1i5pbnqgA58XDm07xXTPxfZUzcPq9r7+SKYJseosjMF6lk=" #uuid.uuid4().hex

# Log
logging.basicConfig(level=logging.INFO)

# Register des modules
app.register_blueprint(csoMain)
app.register_blueprint(csoGestion, url_prefix='/admin')
app.register_blueprint(csoNginx, url_prefix='/nginx')

@app.before_request
def csrf_protect():
    """
    Test if CSRF if request is POST and if CSRF is matching
    """
    if request.method == "POST" and "/nginx/" not in request.path:
        token = session.pop('_csrf_token', None)
        if not token or token != request.form.get('_csrf_token'):
            abort(403)

def generate_csrf_token():
    """
    Function to generate a new csrf_token
    """
    if '_csrf_token' not in session:
        session['_csrf_token'] = uuid.uuid4().hex
    return session['_csrf_token']

# Inject the function into jinja available function
app.jinja_env.globals['csrf_token'] = generate_csrf_token

if __name__ == "__main__":
    app.jinja_env.auto_reload = True
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.run(host="0.0.0.0", debug=True)
    