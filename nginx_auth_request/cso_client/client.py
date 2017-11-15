import base64, json, hashlib
from bottle import route, run, template, request, response, HTTPResponse, redirect

security_key = "mWgBV6mKZ3nwhwpvMBxx"

@route('/checkAuth', method='POST')
def index():
    signature = request.forms.get("signature")
    values = request.forms.get("values")
    if(do_login(values, signature)):
        return redirect('/')
    else:
        return HTTPResponse(status=401)

@route("/auth")
def auth():
    if request.get_cookie("auth_username", secret=security_key):
        return HTTPResponse(status=200)
    else:
        return HTTPResponse(status=401)

def do_login(jsonValues, securityKey):
    try:
        values = json.loads(base64.b64decode(jsonValues))
        values["key"] = security_key
        mySecurityKey = hashlib.sha512(json.dumps(values, separators=(',',':'))).hexdigest()
        values['key'] = ""
        if securityKey == mySecurityKey:
            set_cookie(values)
            return True
        else:
            expire_cookie()
            return False
    except Exception as e:
        expire_cookie()
        return False

def set_cookie(values):
    response.set_cookie('auth_username', values["username"], httponly=True, secret=security_key)
    response.set_cookie('auth_group', values["group"], httponly=True, secret=security_key)
    response.set_cookie('auth_level', values["level"], httponly=True, secret=security_key)

def expire_cookie():
    response.set_cookie('auth_username', "", expires=0, secret=security_key)
    response.set_cookie('auth_group', "", expires=0, secret=security_key)
    response.set_cookie('auth_level', "", expires=0, secret=security_key)


run(host='localhost', port=8000)