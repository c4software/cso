import base64, json, hashlib, sys
from bottle import route, run, template, request, response, HTTPResponse, redirect

if len(sys.argv) < 2:
    print("To use the cso_client you need to provide a CSO app key. \r\nExample : {0} mWgBV6mKZ3nwhwpvMBxx".format(sys.argv[0]))
    sys.exit()

cso_app_key = sys.argv[1]

@route('/checkAuth', method='POST')
def checkAuth():
    signature = request.forms.get("signature")
    values = request.forms.get("values")
    if do_login(values, signature):
        return redirect('/')
    else:
        return HTTPResponse(status=401)

@route("/auth")
def auth():
    if request.get_cookie("auth_username", secret=cso_app_key):
        return HTTPResponse(status=200)
    else:
        return HTTPResponse(status=401)

def do_login(json_values, remote_hash):
    try:
        values = json.loads(base64.b64decode(json_values))
        values["key"] = cso_app_key
        my_hash = hashlib.sha512(json.dumps(values, separators=(',',':'))).hexdigest()
        values['key'] = ""
        if remote_hash == my_hash:
            set_cookie(values)
            return True
        else:
            expire_cookie()
            return False
    except Exception as e:
        expire_cookie()
        return False

def set_cookie(values):
    response.set_cookie('auth_username', values["username"], httponly=True, secret=cso_app_key)
    response.set_cookie('auth_group', values["group"], httponly=True, secret=cso_app_key)
    response.set_cookie('auth_level', values["level"], httponly=True, secret=cso_app_key)

def expire_cookie():
    response.set_cookie('auth_username', "", expires=0, secret=cso_app_key)
    response.set_cookie('auth_group', "", expires=0, secret=cso_app_key)
    response.set_cookie('auth_level', "", expires=0, secret=cso_app_key)


run(host='localhost', port=8000)