from models import Application

def get_app(app_name):
    """
    Return the requested in param
    """
    app = Application.query.filter(Application.nom == app_name).first()
    if app is not None:
        return app
    else:
        return None