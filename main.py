from flask import Flask, render_template, request
from modules.csoMain.views import csoMain
from modules.csoGestion.views import csoGestion

app = Flask(__name__)
app.secret_key = 'li4Q~wNV7%RO?3=r.s|am^3>V:.cY22N%*>+%i=p/B6!1-HMv!/a8w@]Fk2n'

#register des modules
app.register_blueprint(csoMain)
app.register_blueprint(csoGestion, url_prefix='/admin')

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
